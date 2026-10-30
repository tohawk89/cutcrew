import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, ToolCallResult } from 'claude-code'

import type { Floor, RoleId } from '../types'
import {
  NOISY,
  RAW_DENY,
  ROLES,
  alertIn,
  classify,
  emptyFloor,
  endJob,
  projectOf,
  roleName,
  startJob,
  touchesRaw,
  trimOutput,
  writesRawFile,
} from './crew'
import type { Job } from './crew'
import { drawFloor } from './sprites'

const PANE = 'studio-crew'
const floorAtom = atom({ plugin: 'studio-crew', key: 'floor' } as const, emptyFloor())
const selectedAtom = atom({ plugin: 'studio-crew', key: 'selected' } as const, null)
const trimAtom = atom({ plugin: 'studio-crew', key: 'isTrimOn' } as const, true)

/** A step that runs this long gets a toast when it finishes. */
const LONG_STEP_MS = 45_000

const setFloor = ($: EngineInterface, fn: (f: Floor) => Floor) => update($, floorAtom, f => fn(f ?? emptyFloor()))

async function playDing($: EngineInterface) {
  const cwd = await $.session.cwd()
  if (/^[A-Za-z]:/.test(cwd)) {
    // $.audio.play has no player on Windows; PowerShell's SoundPlayer does.
    const wav = `${$.plugin.root}/sounds/ding.wav`.replace(/\//g, '\\').replace(/'/g, "''")
    await $.process.run(
      ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', `(New-Object Media.SoundPlayer '${wav}').PlaySync()`],
      { timeoutMs: 10_000 },
    )
    return
  }
  await $.audio.play({ asset: 'sounds/ding.wav' })
}

const outputOf = (result: unknown) => {
  const r = (result ?? {}) as { stdout?: unknown; stderr?: unknown }
  return `${typeof r.stdout === 'string' ? r.stdout : ''}\n${typeof r.stderr === 'string' ? r.stderr : ''}`
}

/** A noisy shell result with its routine lines cut, the full log kept on disk. */
async function trimmed<R extends ToolCallResult<'Bash'> | ToolCallResult<'PowerShell'>>(
  $: EngineInterface,
  command: string,
  toolUseId: string | undefined,
  isBackground: boolean,
  ran: R,
): Promise<R> {
  if (ran.deny !== undefined || ran.isError === true || isBackground) return ran
  if (!NOISY.test(command.replace(/\\/g, '/')) || !(await read($, trimAtom))) return ran

  const result = ran.result
  if (result.persistedOutputPath !== undefined) return ran
  const out = trimOutput(result.stdout)
  const err = trimOutput(result.stderr)
  if (out.hidden + err.hidden === 0) return ran

  let saved = ''
  try {
    const path = `${await $.session.cwd()}/.crew-logs/${toolUseId ?? Date.now()}.log`
    await $.fs.write(path, `$ ${command}\n\n--- stdout ---\n${result.stdout}\n\n--- stderr ---\n${result.stderr}\n`)
    saved = ` Full log: ${path}`
  } catch {
    saved = ' (full log could not be saved)'
  }
  const note = `[studio-crew trimmed ${out.hidden + err.hidden} routine lines.${saved}]`

  return {
    result: { ...result, stdout: `${out.text}\n${note}`, stderr: err.text },
    ...(ran.context ? { context: ran.context } : {}),
  } as R
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'crew',
      description: 'Studio crew pane. /crew opens it, /crew trim on|off sets log trimming, /crew reset clears the floor',
      argumentHint: '[trim on|off | reset]',
    })
    const stored = await $.store.get('trim')
    if (typeof stored === 'boolean') await update($, trimAtom, () => stored)
    void $.ui.open({ id: PANE, title: 'Studio crew' })

    return next(e)
  })

  on('command.run', { command: 'crew' }, async ($, e) => {
    const args = e.args.trim().toLowerCase()
    if (args === 'trim on' || args === 'trim off') {
      const isOn = args === 'trim on'
      await update($, trimAtom, () => isOn)
      await $.store.set('trim', isOn)
      return { text: `Studio crew: log trimming ${isOn ? 'on' : 'off'}.` }
    }
    if (args === 'reset') {
      await update($, floorAtom, () => emptyFloor())
      return { text: 'Studio crew: floor cleared.' }
    }
    await $.ui.open({ id: PANE, title: 'Studio crew' })
    return { text: 'Studio crew pane opened.' }
  })

  // ---- raw/ guard ---------------------------------------------------------

  const GUARD_FAILED = 'studio-crew: its raw/ guard failed.'
  on('tool.call', { tool: 'Write' }, ($, e, next) => (writesRawFile(e.file_path) ? { deny: RAW_DENY } : next(e))).catch(
    ($, e, next) => (next.called ? next(e) : { deny: GUARD_FAILED }),
  )
  on('tool.call', { tool: 'Edit' }, ($, e, next) => (writesRawFile(e.file_path) ? { deny: RAW_DENY } : next(e))).catch(
    ($, e, next) => (next.called ? next(e) : { deny: GUARD_FAILED }),
  )
  on('tool.call', { tool: 'NotebookEdit' }, ($, e, next) =>
    writesRawFile(e.notebook_path) ? { deny: RAW_DENY } : next(e),
  ).catch(($, e, next) => (next.called ? next(e) : { deny: GUARD_FAILED }))
  on('tool.call', { tool: 'Bash' }, ($, e, next) => (touchesRaw(e.command) ? { deny: RAW_DENY } : next(e))).catch(
    ($, e, next) => (next.called ? next(e) : { deny: GUARD_FAILED }),
  )
  on('tool.call', { tool: 'PowerShell' }, ($, e, next) => (touchesRaw(e.command) ? { deny: RAW_DENY } : next(e))).catch(
    ($, e, next) => (next.called ? next(e) : { deny: GUARD_FAILED }),
  )

  // ---- shorter logs for noisy commands -------------------------------------

  on('tool.call', { tool: 'Bash' }, async ($, e, next) =>
    trimmed($, e.command, e.tool_use_id, e.run_in_background === true, await next(e)),
  ).catch(($, e, next) => next(e))
  on('tool.call', { tool: 'PowerShell' }, async ($, e, next) =>
    trimmed($, e.command, e.tool_use_id, e.run_in_background === true, await next(e)),
  ).catch(($, e, next) => next(e))

  // ---- the crew at work ----------------------------------------------------

  on('prompt.submit', async ($, e, next) => {
    const now = await $.clock.now()
    await setFloor($, f => ({
      ...startJob(f, { role: 'editor', line: 'Reading your request' }, now),
      helpers: f.helpers.filter(h => !h.isDone),
    }))
    return next(e)
  }).catch(($, e, next) => next(e))

  on('tool.call', async ($, e, next) => {
    const input = e as unknown as Record<string, unknown>
    const tool = String(e.tool)
    const job: Job = classify(tool, input)
    const now = await $.clock.now()
    const project = projectOf(input)

    if (e.agentId !== undefined) {
      const agentId = e.agentId
      await setFloor($, f => ({
        ...f,
        helpers: f.helpers.map(h => (h.id === agentId ? { ...h, line: job.line } : h)),
      }))
      return next(e)
    }

    await setFloor($, f => ({ ...startJob(f, job, now), project: project ?? f.project }))
    $.ui.status(`${roleName(job.role)}: ${job.line}…`)

    const ran = await next(e)

    const isOk = ran.deny === undefined && ran.isError !== true
    const command = typeof input.command === 'string' ? input.command.replace(/\\/g, '/') : ''
    const isSoundCheck = /scripts\/(audio\.py\s+(check|master)|finish\.py)/.test(command)
    const isDelivery = isOk && /scripts\/finish\.py/.test(command) && input.run_in_background !== true
    const alert = isSoundCheck && ran.deny === undefined ? alertIn(outputOf(ran.result) + (ran.text ?? '')) : undefined
    const doneAt = await $.clock.now()

    await setFloor($, f => {
      let after = endJob(f, job, isOk)
      if (alert !== undefined) {
        after = { ...after, crew: { ...after.crew, sound: { ...after.crew.sound, alert } } }
      }
      if (isDelivery && alert === null) {
        after = { ...after, delivered: after.delivered + 1, deliveredAt: doneAt }
      }
      return after
    })
    $.ui.status(undefined)

    if (alert) {
      $.ui.toast(`Sound: check failed — ${alert}`)
    } else if (isDelivery && alert === null) {
      $.ui.toast('Finisher: final video delivered')
      void playDing($).catch(() => undefined)
    } else if (doneAt - now > LONG_STEP_MS) {
      const secs = Math.round((doneAt - now) / 1000)
      $.ui.toast(`${roleName(job.role)} finished: ${job.line} (${Math.floor(secs / 60)}m ${secs % 60}s)`)
    }

    return ran
  }).catch(($, e, next) => next(e))

  on('agent.spawn', async ($, e, next) => {
    const ran = await next(e)
    if (ran.agentId !== undefined) {
      const helper = {
        id: ran.agentId,
        name: e.name ?? e.subagentType ?? 'Helper',
        line: e.description ?? 'Helping out',
        isDone: false,
        arrivedAt: await $.clock.now(),
      }
      await setFloor($, f => ({ ...f, helpers: [...f.helpers, helper].slice(-8) }))
    }
    return ran
  }).catch(($, e, next) => next(e))

  on('turn.complete', async ($, e, next) => {
    const agentId = e.agentId
    if (agentId !== undefined) {
      await setFloor($, f => ({
        ...f,
        helpers: f.helpers.map(h => (h.id === agentId ? { ...h, isDone: true, line: 'Finished' } : h)),
      }))
      return next(e)
    }
    await setFloor($, f => {
      const crew = { ...f.crew }
      for (const r of ROLES) crew[r.id] = { ...crew[r.id], mood: 'idle', line: '' }
      crew.editor = { ...crew.editor, mood: 'working', line: 'Your turn!' }
      return { ...f, crew }
    })
    $.ui.status(undefined)
    return next(e)
  }).catch(($, e, next) => next(e))

  // ---- drawing -------------------------------------------------------------

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const floor = (await read($, floorAtom)) ?? emptyFloor()
    const selected = (await read($, selectedAtom)) as RoleId | null
    const isTrimOn = (await read($, trimAtom)) ?? true
    const pick = (id: RoleId) => update($, selectedAtom, cur => (cur === id ? null : id))

    if (e.surface === 'terminal') {
      const { Box, Text } = $.ui.resolve(e)
      return (
        <Box flexDirection="column">
          {ROLES.map(r => {
            const w = floor.crew[r.id]
            return (
              <Text dimColor={w.mood === 'idle' && !w.alert}>
                {floor.holder === r.id ? '▣ ' : '  '}
                {r.name.padEnd(12)}
                {w.mood === 'working' ? w.line : w.alert ? `!! ${w.alert}` : (w.log[w.log.length - 1] ?? 'idle')}
              </Text>
            )
          })}
          <Text dimColor>Delivered: {floor.delivered}</Text>
        </Box>
      )
    }

    const { Box, Text, Button, Svg } = $.ui.resolve(e)
    const now = await $.clock.now()
    const pickedLog = selected ? floor.crew[selected] : undefined

    return (
      <Box flexDirection="column" gap={1}>
        <Svg
          source={drawFloor(floor, now, selected)}
          alt={`Studio crew. ${roleName(floor.holder)} has the video. Delivered: ${floor.delivered}.`}
          isInteractive
        />
        <Box flexDirection="row" flexWrap="wrap" gap={1}>
          {ROLES.map(r => (
            <Button key={`pick-${r.id}`} label={r.name} variant={selected === r.id ? 'primary' : 'secondary'} onPress={() => pick(r.id)} />
          ))}
          <Button
            key="trim"
            label={isTrimOn ? 'Logs: trimmed' : 'Logs: full'}
            onPress={async () => {
              const isOn = !isTrimOn
              await update($, trimAtom, () => isOn)
              await $.store.set('trim', isOn)
            }}
          />
        </Box>
        {selected && pickedLog && (
          <Box flexDirection="column">
            <Text bold>{roleName(selected)}</Text>
            {pickedLog.alert && <Text color="red">!! {pickedLog.alert}</Text>}
            {pickedLog.log.length === 0 && <Text dimColor>No jobs yet this session.</Text>}
            {pickedLog.log.map(line => (
              <Text>{line}</Text>
            ))}
          </Box>
        )}
      </Box>
    )
  })
}

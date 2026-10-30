import type { Floor, RoleId, Worker } from '../types'

export const ROLES: readonly { id: RoleId; name: string }[] = [
  { id: 'editor', name: 'Editor' },
  { id: 'transcriber', name: 'Transcriber' },
  { id: 'cutter', name: 'Cutter' },
  { id: 'researcher', name: 'Researcher' },
  { id: 'animator', name: 'Animator' },
  { id: 'sound', name: 'Sound' },
  { id: 'finisher', name: 'Finisher' },
]

export const roleName = (id: RoleId) => ROLES.find(r => r.id === id)?.name ?? id

export type Job = { role: RoleId; line: string }

const norm = (s: string) => s.replace(/\\/g, '/')

const baseName = (p: string) => p.split('/').filter(Boolean).pop() ?? p

const MEDIA = /[^\s"'/]+\.(mp4|mkv|mov|webm|wav|mp3|m4a|json|srt|png|html)\b/i

const mediaIn = (s: string) => s.match(MEDIA)?.[0] ?? ''

/** Which crew member a tool call belongs to, and what their speech bubble says. */
export function classify(tool: string, input: Record<string, unknown>): Job {
  const command = typeof input.command === 'string' ? norm(input.command) : ''
  if (command !== '') {
    return classifyCommand(command)
  }

  const path = norm(String(input.file_path ?? input.notebook_path ?? input.path ?? ''))
  const verb = tool === 'Read' ? 'Reading' : tool === 'Write' ? 'Writing' : tool === 'Edit' ? 'Editing' : 'Looking at'

  if (/Claude_Browser|claude-in-chrome|WebSearch|WebFetch/.test(tool)) {
    const url = typeof input.url === 'string' ? input.url : ''
    const host = url.match(/^(?:https?:\/\/)?([^/]+)/)?.[1]
    return { role: 'researcher', line: host ? `Browsing ${host}` : 'Researching on the web' }
  }
  if (tool === 'Skill') {
    const skill = String(input.skill ?? '')
    if (/hyperframes|motion-graphics|media-use/.test(skill)) {
      return { role: 'animator', line: `Opening ${skill}` }
    }
    return { role: 'editor', line: `Opening ${skill || 'a skill'}` }
  }
  if (/(^|\/)animations\//.test(path)) {
    return { role: 'animator', line: `${verb} ${baseName(path)}` }
  }
  if (/(^|\/)library\/(music|sfx)\//.test(path) || /CREDITS\.md$/i.test(path)) {
    return { role: 'sound', line: `${verb} ${baseName(path)}` }
  }
  if (/(^|\/)assets\/facts\//.test(path)) {
    return { role: 'researcher', line: `${verb} ${baseName(path)}` }
  }
  if (path !== '') {
    return { role: 'editor', line: `${verb} ${baseName(path)}` }
  }
  if (tool === 'Agent') {
    return { role: 'editor', line: 'Calling in a helper' }
  }

  return { role: 'editor', line: 'Thinking it through' }
}

export function classifyCommand(command: string): Job {
  const file = mediaIn(command)
  const on = file ? ` ${file}` : ''

  if (/scripts\/transcribe\.py/.test(command)) return { role: 'transcriber', line: `Listening to${on || ' the take'}` }
  if (/scripts\/sync\.py/.test(command)) return { role: 'transcriber', line: 'Syncing voice to video' }
  if (/scripts\/cut\.py\s+suggest/.test(command)) return { role: 'cutter', line: 'Finding pauses and ums' }
  if (/scripts\/cut\.py\s+render[^\n]*--draft/.test(command)) return { role: 'cutter', line: 'Rendering the draft' }
  if (/scripts\/cut\.py\s+render/.test(command)) return { role: 'cutter', line: 'Rendering full quality' }
  if (/scripts\/cut\.py/.test(command)) return { role: 'cutter', line: 'Cutting' }
  if (/scripts\/audio\.py\s+analyze/.test(command)) return { role: 'sound', line: 'Profiling the sound' }
  if (/scripts\/audio\.py\s+master/.test(command)) return { role: 'sound', line: 'Mastering the mix' }
  if (/scripts\/audio\.py\s+check/.test(command)) return { role: 'sound', line: 'Running the sound check' }
  if (/scripts\/audio\.py/.test(command)) return { role: 'sound', line: 'Working on the sound' }
  if (/scripts\/grab\.py/.test(command)) return { role: 'researcher', line: 'Screenshotting a source' }
  if (/scripts\/finish\.py/.test(command)) return { role: 'finisher', line: 'Exporting the final video' }
  if (/hyperframes|(^|[\s/])animations\//.test(command)) {
    return { role: 'animator', line: /\brender\b/.test(command) ? 'Rendering a graphic' : 'Building a graphic' }
  }
  if (/library\/(music|sfx)/.test(command)) return { role: 'sound', line: 'Sorting the music library' }
  if (/\bffprobe\b/.test(command)) return { role: 'finisher', line: `Inspecting${on || ' the video'}` }
  if (/\bffmpeg\b/.test(command)) {
    return { role: 'finisher', line: /-frames:v/.test(command) ? 'Checking frames' : 'Processing video' }
  }

  const first = command.trim().split(/\s+/)[0] ?? ''
  return { role: 'editor', line: `Running ${baseName(first).slice(0, 24) || 'a command'}` }
}

/** The project a tool call is about, when its paths name one. */
export function projectOf(input: Record<string, unknown>): string | undefined {
  const text = norm(
    [input.command, input.file_path, input.path, input.notebook_path].filter(v => typeof v === 'string').join(' '),
  )
  return text.match(/projects\/([^/\s"']+)/)?.[1]
}

// ---- raw/ guard -----------------------------------------------------------

const RAW_FILE = /(^|\/)projects\/[^/]+\/raw\//i
const RAW_REF = /projects\/[^/\s"']+\/raw(\/|["'\s]|$)|(^|[\s"'])raw\//i
const DESTRUCTIVE =
  /(^|[\s;&|(])(rm|del|erase|rmdir|rd|mv|move|ren|rename|truncate|shred|Remove-Item|Move-Item|Rename-Item|Clear-Content|Set-Content|Add-Content|Out-File|New-Item|ri|mi|rni)(?=\s|$)/i
const REDIRECT_INTO_RAW = />>?\s*["']?[^\s"']*raw\//i
const COPIERS = /(^|[\s;&|(])(ffmpeg|cp|copy|xcopy|robocopy|Copy-Item|cpi)(?=\s|$)/i

export const RAW_DENY =
  'studio-crew: projects/<name>/raw/ holds the original recordings and is never changed. Write to renders/ or assets/ instead. ' +
  'To add a recording, create the folder (New-Item -ItemType Directory) and hard-link it in (New-Item -ItemType HardLink, no -Force).'

/**
 * Adding to raw/ is allowed: creating the folder, or hard-linking a new recording in.
 * A hard link without -Force fails when the file already exists, so it can never overwrite.
 */
export function addsToRaw(statement: string): boolean {
  if (!/^\s*(New-Item|ni)(?=\s)/i.test(statement)) return false
  const type = statement.match(/-ItemType\s+["']?(\w+)/i)?.[1]?.toLowerCase()
  if (type === 'directory') return true
  if (type === 'hardlink') return !/\s-Force\b/i.test(statement)
  return false
}

/** True when a file tool would write inside a project's raw/ folder. */
export const writesRawFile = (path: string) => RAW_FILE.test(norm(path))

/**
 * Best effort: true when a shell command would delete, move, overwrite or
 * create something inside raw/. Reading from raw/ (transcribe, ffmpeg -i) passes.
 */
export function touchesRaw(rawCommand: string): boolean {
  // Drop the statements that only add to raw/; the rest of the command is checked as before.
  const command = norm(rawCommand)
    .split(/\r?\n|;|&&|\|\|?/)
    .filter(statement => !addsToRaw(statement))
    .join(' ; ')
  if (!RAW_REF.test(command)) return false
  if (DESTRUCTIVE.test(command) || REDIRECT_INTO_RAW.test(command)) return true
  if (COPIERS.test(command)) {
    const args = command.split(/\s+/).filter(a => a !== '' && !a.startsWith('-'))
    const last = (args[args.length - 1] ?? '').replace(/["']/g, '')
    return /(^|\/)raw(\/|$)/i.test(last)
  }
  return false
}

// ---- log trimming ---------------------------------------------------------

export const NOISY = /\b(ffmpeg|ffprobe|npx|npm|pip)\b|scripts\/\w+\.py|hyperframes/

const KEEP =
  /error|warn|fail|!!|traceback|exception|invalid|not found|denied|lufs|dbtp|\blra\b|peak|confidence|runtime|duration|saved|wrote|written|->|→|\bdone\b/i

const HEAD = 10
const TAIL = 30
const MAX_KEPT_MIDDLE = 40

/** Collapses carriage-return progress bars, then keeps the head, the tail and every important line. */
export function trimOutput(text: string, limit = 60): { text: string; hidden: number } {
  const lines = text.split(/\r?\n/).map(line => {
    const parts = line.split('\r').filter(p => p.trim() !== '')
    return parts[parts.length - 1] ?? ''
  })
  const collapsed = lines.join('\n')
  if (lines.length <= limit) {
    return { text: collapsed.length < text.length ? collapsed : text, hidden: 0 }
  }

  const middle = lines.slice(HEAD, lines.length - TAIL)
  const kept = middle.filter(line => KEEP.test(line)).slice(0, MAX_KEPT_MIDDLE)
  const hidden = middle.length - kept.length
  const out = [...lines.slice(0, HEAD), ...kept, `… ${hidden} routine lines hidden …`, ...lines.slice(lines.length - TAIL)]

  return { text: out.join('\n'), hidden }
}

/** The first `!!` line of a sound check, or null when it passed. */
export const alertIn = (output: string) =>
  output.split(/\r?\n/).find(line => line.includes('!!'))?.trim() ?? null

// ---- floor state ----------------------------------------------------------

const worker = (): Worker => ({ mood: 'idle', line: '', log: [], alert: null })

export function emptyFloor(): Floor {
  return {
    crew: {
      editor: worker(),
      transcriber: worker(),
      cutter: worker(),
      researcher: worker(),
      animator: worker(),
      sound: worker(),
      finisher: worker(),
    },
    holder: 'editor',
    handoff: null,
    helpers: [],
    delivered: 0,
    deliveredAt: 0,
    project: '',
  }
}

export function startJob(floor: Floor, job: Job, now: number): Floor {
  const crew = { ...floor.crew, [job.role]: { ...floor.crew[job.role], mood: 'working' as const, line: job.line } }
  const isHandoff = floor.holder !== job.role
  return {
    ...floor,
    crew,
    holder: job.role,
    handoff: isHandoff ? { from: floor.holder, to: job.role, at: now } : floor.handoff,
  }
}

export function endJob(floor: Floor, job: Job, isOk: boolean): Floor {
  const was = floor.crew[job.role]
  const log = [...was.log, `${isOk ? '✓' : '✗'} ${job.line}`].slice(-6)
  return { ...floor, crew: { ...floor.crew, [job.role]: { ...was, mood: 'idle', line: '', log } } }
}

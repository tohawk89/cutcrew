import { describe, expect, mock, test } from 'claude-code/testing'

import { classifyCommand, touchesRaw, trimOutput } from '../hooks/crew'

const PANE = {
  title: 'Studio crew',
  isFocused: false,
  bodyColumns: 80,
  placement: 'dock' as const,
  scroll: { offset: 0, bodyRows: 40 },
  view: {},
}

describe('studio-crew', () => {
  test('commands go to the right crew member', async () => {
    expect(classifyCommand('.venv/Scripts/python.exe scripts/transcribe.py projects/x/raw/a.mp4').role).toBe('transcriber')
    expect(classifyCommand('python scripts/cut.py render projects/x/edl.json --draft').line).toBe('Rendering the draft')
    expect(classifyCommand('python scripts/audio.py check out.mp4').role).toBe('sound')
    expect(classifyCommand('python scripts/finish.py projects/x/renders/edl-cut.mp4').role).toBe('finisher')
    expect(classifyCommand('npx hyperframes render').role).toBe('animator')
    expect(classifyCommand('ls').role).toBe('editor')
  })

  test('the raw/ guard blocks changes and lets reads through', async () => {
    expect(touchesRaw('Remove-Item projects\\x\\raw\\a.mp4')).toBe(true)
    expect(touchesRaw('mv projects/x/raw/a.mp4 projects/x/assets/')).toBe(true)
    expect(touchesRaw('ffmpeg -i in.mp4 projects/x/raw/out.mp4')).toBe(true)
    expect(touchesRaw('echo hi > projects/x/raw/note.txt')).toBe(true)
    expect(touchesRaw('python scripts/transcribe.py projects/x/raw/a.mp4')).toBe(false)
    expect(touchesRaw('ffmpeg -i projects/x/raw/a.mp4 -frames:v 1 check.png')).toBe(false)
    expect(touchesRaw('Copy-Item projects/x/raw/a.mp4 projects/x/assets/a.mp4')).toBe(false)
  })

  test('the raw/ guard lets recordings be added but never overwritten', async () => {
    expect(touchesRaw('New-Item -ItemType Directory -Force projects\\x\\raw | Out-Null')).toBe(false)
    expect(touchesRaw('New-Item -ItemType HardLink -Path projects\\x\\raw\\camera.mp4 -Target "D:\\Recordings\\x\\a.mp4"')).toBe(false)
    expect(
      touchesRaw('New-Item -ItemType Directory projects/x/raw; New-Item -ItemType HardLink -Path projects/x/raw/audio.m4a -Target b.m4a'),
    ).toBe(false)
    expect(touchesRaw('New-Item -ItemType HardLink -Force -Path projects/x/raw/camera.mp4 -Target a.mp4')).toBe(true)
    expect(touchesRaw('New-Item -ItemType File projects/x/raw/note.txt')).toBe(true)
    expect(touchesRaw('New-Item -ItemType Directory projects/x/raw; Remove-Item projects/x/raw/a.mp4')).toBe(true)
    expect(touchesRaw('Copy-Item a.mp4 projects/x/raw/a.mp4')).toBe(true)
  })

  test('the guard refuses a Write into raw/', async ($, on) => {
    on('tool.call', () => ({ result: { type: 'create', filePath: 'x', content: 'x', structuredPatch: [], originalFile: null } }))
    mock.clock(on)
    mock.store(on)
    const denied = await $.tool.call({ tool: 'Write', file_path: 'F:/video-editor/projects/x/raw/a.txt', content: 'x' })
    expect(JSON.stringify(denied)).toContain('original recordings')
    const allowed = await $.tool.call({ tool: 'Write', file_path: 'F:/video-editor/projects/x/renders/a.txt', content: 'x' })
    expect(JSON.stringify(allowed)).not.toContain('original recordings')
  })

  test('long ffmpeg logs are trimmed but keep the important lines', async () => {
    const lines = Array.from({ length: 200 }, (_, i) => `frame=${i} fps=30 q=28.0 size=1kB`)
    lines[120] = 'Output loudness: -14.1 LUFS, true peak -2.3 dBTP'
    const { text, hidden } = trimOutput(lines.join('\n'))
    expect(hidden > 100).toBe(true)
    expect(text.includes('LUFS')).toBe(true)
    expect(trimOutput('short\noutput').hidden).toBe(0)
  })

  test('the pane draws the pixel floor on desktop and text on terminal', async ($, on) => {
    mock.clock(on)
    mock.store(on)
    const desk = await $.ui.mount({ plugin: 'studio-crew', surface: 'desktop', component: 'Pane', requestId: 'studio-crew', props: PANE })
    expect(await desk.find({ type: 'Svg' })).toBeDefined()
    await desk.press({ key: 'pick-sound' })
    expect(await desk.find({ type: 'Text', text: 'No jobs yet this session.' })).toBeDefined()

    const term = await $.ui.mount({ plugin: 'studio-crew', surface: 'terminal', component: 'Pane', requestId: 'studio-crew', props: PANE })
    expect(await term.find({ type: 'Text', text: /Delivered: 0/ })).toBeDefined()
  })
})

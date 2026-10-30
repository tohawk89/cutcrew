import type { Floor, Helper, RoleId } from '../types'
import { ROLES } from './crew'

// Pixel art: each string row is one line of pixels, each letter a colour key,
// '.' transparent. One pixel is drawn as a P x P square.
const P = 4

const BODY = [
  '....HHHH....',
  '..HHHHHHHH..',
  '..HHSSSSHH..',
  '..HSSSSSSH..',
  '..SSESSESS..',
  '..SSSSSSSS..',
  '...SSMMSS...',
  '....SSSS....',
  '..TTTTTTTT..',
  '.TTTTTTTTTT.',
  '.STTTTTTTTS.',
  '.STTTTTTTTS.',
  '..TTTTTTTT..',
  '..PPP..PPP..',
  '..PPP..PPP..',
  '..BBB..BBB..',
]

type Look = {
  hair: string
  skin: string
  shirt: string
  pants: string
  /** Rows painted over BODY, by row index. */
  extra: Record<number, string>
  /** Colours for the letters `extra` uses. */
  ink: Record<string, string>
  prop: string[]
}

const LOOKS: Record<RoleId | 'helper', Look> = {
  editor: {
    hair: '#3b2a20', skin: '#f2c7a5', shirt: '#7b5cd6', pants: '#2e2a4f',
    extra: { 0: '...KKKKKK...', 1: '..KKKKKKKK..' },
    ink: { K: '#5a1f3d' },
    prop: ['..LLLLL.', '..LDDDL.', '..LDDDL.', '..LLLLL.', '.LLLLLLL'],
  },
  transcriber: {
    hair: '#16120f', skin: '#c98e62', shirt: '#2fa39a', pants: '#21364a',
    extra: { 0: '...KKKKKK...', 1: '..K......K..', 3: '.KK......KK.', 4: '.KK......KK.', 5: '.........K..', 6: '.........KK.' },
    ink: { K: '#2b2b2b' },
    prop: ['...mm...', '..mmmm..', '..mmmm..', '...mm...', '....k...', '..kkkk..'],
  },
  cutter: {
    hair: '#8a3b12', skin: '#f5d0b0', shirt: '#e0663a', pants: '#3a2a22',
    extra: { 1: '..RRRRRRRR..', 2: '..R......RRR' },
    ink: { R: '#c62828' },
    prop: ['.oo..oo.', '.o.oo.o.', '..oooo..', '...ss...', '..s..s..', '.s....s.'],
  },
  researcher: {
    hair: '#d9b24a', skin: '#f2c7a5', shirt: '#3d7fd9', pants: '#2b2f3a',
    extra: { 4: '..GG.GG.GG..' },
    ink: { G: '#1b1b1b' },
    prop: ['..ggg...', '.g...g..', '.g...g..', '..ggg...', '.....b..', '......b.'],
  },
  animator: {
    hair: '#5b2d82', skin: '#e8b48f', shirt: '#e05297', pants: '#2c2340',
    extra: { 0: '....CWWC....', 1: '..CCCCCCCC..', 2: '..CCCCCCCC..' },
    ink: { C: '#f2b632', W: '#ffffff' },
    prop: ['.pppppp.', 'pRpGpBpp', 'pppppp..', 'pYpp....', '.pp.....'],
  },
  sound: {
    hair: '#101010', skin: '#a8714d', shirt: '#43b04a', pants: '#1f2a1f',
    extra: { 0: '...KKKKKK...', 1: '..K......K..', 2: '.KK......KK.', 3: '.KK......KK.', 4: '.KK......KK.' },
    ink: { K: '#d13b3b' },
    prop: ['.kkkk...', '.kWWk...', '.kkkk...', '.kWWk...', '.kWWk...', '.kkkk...'],
  },
  finisher: {
    hair: '#6b4a2b', skin: '#f2c7a5', shirt: '#30343f', pants: '#16181d',
    extra: { 0: '...CCCCCC...', 1: '..CCCCCCCCCC' },
    ink: { C: '#e6b422' },
    prop: ['wkwkwkw.', 'kkkkkkk.', 'kwwwwwk.', 'kwwwwwk.', 'kkkkkkk.'],
  },
  helper: {
    hair: '#7a7a7a', skin: '#e9c2a0', shirt: '#8aa0b8', pants: '#33404d',
    extra: { 8: '..TTTTTYTT..' },
    ink: { Y: '#f2d14b' },
    prop: [],
  },
}

const PROP_INK: Record<string, string> = {
  L: '#c9ced6', D: '#4aa3ff', m: '#9aa3ad', k: '#2b2b2b', o: '#d0d4da', s: '#9aa3ad',
  g: '#c9a227', b: '#6b4a2b', p: '#d9b48a', R: '#e53935', G: '#43a047', B: '#1e88e5',
  Y: '#fdd835', W: '#e0e0e0', w: '#f5f5f5',
}

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

const clip = (s: string, n: number) => (s.length > n ? `${s.slice(0, n - 1)}…` : s)

/** Rows of colour keys to <rect>s, joining horizontal runs of one colour. */
function pixels(rows: string[], ink: (key: string) => string | undefined, x0: number, y0: number, size = P): string {
  let out = ''
  rows.forEach((row, y) => {
    let x = 0
    while (x < row.length) {
      const key = row[x]!
      const colour = key === '.' ? undefined : ink(key)
      let run = 1
      while (x + run < row.length && row[x + run] === key) run++
      if (colour !== undefined) {
        out += `<rect x="${x0 + x * size}" y="${y0 + y * size}" width="${run * size}" height="${size}" fill="${colour}"/>`
      }
      x += run
    }
  })
  return out
}

function person(look: Look, x0: number, y0: number): string {
  const rows = BODY.map((row, i) => {
    const over = look.extra[i]
    if (over === undefined) return row
    return [...row].map((c, j) => (over[j] !== undefined && over[j] !== '.' ? over[j] : c)).join('')
  })
  const ink = (key: string) =>
    ({ H: look.hair, S: look.skin, E: '#1a1a1a', M: '#b5524a', T: look.shirt, P: look.pants, B: '#222' })[key] ??
    look.ink[key]
  return pixels(rows, ink, x0, y0)
}

const PACKAGE = ['TTTTTT', 'TttttT', 'TTTTTT', 'TttttT', 'TTTTTT']
const PACKAGE_INK: Record<string, string> = { T: '#c58b4b', t: '#e8c18f' }

const STAR = ['...y...', '..yyy..', 'yyyyyyy', '.yyyyy.', '.yy.yy.', 'y.....y']

const CELL_W = 140
const CELL_H = 150
const COLS = 4

const cellOrigin = (index: number) => ({ x: (index % COLS) * CELL_W, y: Math.floor(index / COLS) * CELL_H })

/** Where the package sits on a role's desk, in floor coordinates. */
function deskSpot(role: RoleId) {
  const { x, y } = cellOrigin(ROLES.findIndex(r => r.id === role))
  return { x: x + 30, y: y + 84 }
}

function bubble(text: string, cx: number, top: number, tone: 'talk' | 'alert'): string {
  const t = clip(text, 19)
  const w = Math.max(40, t.length * 6 + 16)
  // Kept inside its own cell so neighbours never overlap.
  const cellLeft = Math.floor(cx / CELL_W) * CELL_W
  const x = Math.min(Math.max(Math.round(cx - w / 2), cellLeft + 2), cellLeft + CELL_W - 2 - w)
  const fill = tone === 'alert' ? '#ffebee' : '#fffdf5'
  const stroke = tone === 'alert' ? '#d32f2f' : '#1a1a1a'
  return (
    `<g class="pop">` +
    `<rect x="${x}" y="${top}" width="${w}" height="20" fill="${fill}" stroke="${stroke}" stroke-width="2"/>` +
    `<rect x="${cx - 4}" y="${top + 19}" width="8" height="4" fill="${fill}"/>` +
    `<rect x="${cx - 2}" y="${top + 23}" width="4" height="4" fill="${stroke}"/>` +
    `<text x="${cx}" y="${top + 14}" class="say" fill="${tone === 'alert' ? '#b71c1c' : '#1a1a1a'}">${esc(t)}</text>` +
    `</g>`
  )
}

type Draw = { floor: Floor; now: number; selected: RoleId | null }

function station(role: RoleId, name: string, index: number, { floor, now, selected }: Draw): string {
  const w = floor.crew[role]
  const { x, y } = cellOrigin(index)
  const look = LOOKS[role]
  const isWorking = w.mood === 'working'
  const isSleeping = !isWorking && w.log.length === 0 && role !== floor.holder
  const isSelected = selected === role
  const cx = x + CELL_W / 2
  const charX = cx - 24
  const charY = y + 34

  const tip = [name, ...(w.alert ? [`!! ${w.alert}`] : []), ...(w.log.length ? w.log : ['No jobs yet'])].join('\n')

  let out = `<g><title>${esc(tip)}</title>`
  out += `<rect x="${x + 4}" y="${y + 4}" width="${CELL_W - 8}" height="${CELL_H - 8}" fill="${isSelected ? '#3a3f5c' : '#2a2d40'}" stroke="${isSelected ? '#ffd54f' : '#3c4058'}" stroke-width="2"/>`
  out += `<g class="${isWorking ? 'work' : 'rest'}">${person(look, charX, charY)}</g>`
  // Desk in front of the lower body, its prop on top.
  out += `<rect x="${cx - 50}" y="${y + 84}" width="100" height="6" fill="#a8743f"/>`
  out += `<rect x="${cx - 50}" y="${y + 90}" width="100" height="18" fill="#7c5230"/>`
  out += `<rect x="${cx - 46}" y="${y + 108}" width="6" height="6" fill="#5c3b22"/><rect x="${cx + 40}" y="${y + 108}" width="6" height="6" fill="#5c3b22"/>`
  out += `<g class="${isWorking ? 'tap' : ''}">${pixels(look.prop, k => PROP_INK[k], cx + 14, y + 84 - look.prop.length * P)}</g>`

  if (isWorking) {
    out += bubble(w.line, cx, y + 8, 'talk')
  } else if (w.alert) {
    out += `<text x="${cx + 30}" y="${y + 40}" class="bang">!!</text>`
  } else if (isSleeping) {
    out += `<text x="${cx + 22}" y="${y + 36}" class="z">z</text><text x="${cx + 30}" y="${y + 28}" class="z z2">Z</text>`
  }

  if (role === 'finisher' && floor.deliveredAt > 0 && now - floor.deliveredAt < 20000) {
    out += `<g class="star">${pixels(STAR, () => '#ffd54f', cx - 14, y + 10, 4)}</g>`
  }

  out += `<text x="${cx}" y="${y + 128}" class="name">${esc(name)}</text>`
  const sub = isWorking ? 'working…' : w.alert ? 'sound check failed' : w.log.length ? clip(w.log[w.log.length - 1]!, 20) : 'idle'
  out += `<text x="${cx}" y="${y + 141}" class="sub">${esc(sub)}</text>`
  return `${out}</g>`
}

function board(floor: Floor, index: number): string {
  const { x, y } = cellOrigin(index)
  const cx = x + CELL_W / 2
  const reel = ['.kkkk.', 'kwkkwk', 'kkwwkk', 'kkwwkk', 'kwkkwk', '.kkkk.']
  return (
    `<g><title>Videos finished this session: ${floor.delivered}</title>` +
    `<rect x="${x + 4}" y="${y + 4}" width="${CELL_W - 8}" height="${CELL_H - 8}" fill="#1f2233" stroke="#3c4058" stroke-width="2"/>` +
    pixels(reel, k => (k === 'k' ? '#cfd8dc' : '#1f2233'), cx - 18, y + 22, 6) +
    `<text x="${cx}" y="${y + 86}" class="big">${floor.delivered}</text>` +
    `<text x="${cx}" y="${y + 104}" class="sub">delivered</text>` +
    `<text x="${cx}" y="${y + 128}" class="name">${esc(clip(floor.project || 'no project yet', 17))}</text>` +
    `</g>`
  )
}

function helperSpot(h: Helper, slot: number, top: number, now: number): string {
  const x = slot * CELL_W
  const cx = x + CELL_W / 2
  const isNew = now - h.arrivedAt < 3000
  let out = `<g><title>${esc(`${h.name}\n${h.line}`)}</title>`
  out += `<rect x="${x + 4}" y="${top + 4}" width="${CELL_W - 8}" height="${CELL_H - 8}" fill="#262a3b" stroke="#3c4058" stroke-width="2" stroke-dasharray="6 4"/>`
  out += `<g class="${isNew ? 'walkin' : h.isDone ? 'rest' : 'work'}">${person(LOOKS.helper, cx - 24, top + 34)}</g>`
  out += h.isDone
    ? `<text x="${cx + 30}" y="${top + 40}" class="ok">✓</text>`
    : bubble(h.line, cx, top + 8, 'talk')
  out += `<text x="${cx}" y="${top + 128}" class="name">${esc(clip(h.name, 18))}</text>`
  out += `<text x="${cx}" y="${top + 141}" class="sub">${h.isDone ? 'finished' : 'helping…'}</text>`
  return `${out}</g>`
}

function packageLayer(floor: Floor, now: number): string {
  const to = deskSpot(floor.holder)
  const h = floor.handoff
  const isFresh = h !== null && h.to === floor.holder && now - h.at < 1500
  let style = ''
  let cls = ''
  if (isFresh) {
    const from = deskSpot(h.from)
    style = `@keyframes hand{0%{transform:translate(${from.x - to.x}px,${from.y - to.y}px)}50%{transform:translate(${(from.x - to.x) / 2}px,${(from.y - to.y) / 2 - 30}px)}100%{transform:translate(0,0)}}`
    cls = 'fly'
  }
  return (
    (style ? `<style>${style}</style>` : '') +
    `<g class="${cls}"><title>The video is with ${esc(ROLES.find(r => r.id === floor.holder)?.name ?? '')}</title>` +
    pixels(PACKAGE, k => PACKAGE_INK[k], to.x, to.y - PACKAGE.length * P) +
    `</g>`
  )
}

const CSS =
  `.say{font:bold 10px ui-monospace,Consolas,monospace;text-anchor:middle}` +
  `.name{font:bold 12px ui-monospace,Consolas,monospace;fill:#f5f5f5;text-anchor:middle}` +
  `.sub{font:10px ui-monospace,Consolas,monospace;fill:#aab0c8;text-anchor:middle}` +
  `.big{font:bold 28px ui-monospace,Consolas,monospace;fill:#ffd54f;text-anchor:middle}` +
  `.bang{font:bold 18px ui-monospace,Consolas,monospace;fill:#ff5252;animation:bang .5s steps(2) infinite alternate}` +
  `.ok{font:bold 18px ui-monospace,Consolas,monospace;fill:#66bb6a}` +
  `.z{font:bold 11px ui-monospace,Consolas,monospace;fill:#9fa8da;animation:z 2.4s steps(6) infinite}` +
  `.z2{animation-delay:1.2s}` +
  `.work{animation:bob .45s steps(2) infinite alternate}` +
  `.tap{animation:bob .3s steps(2) infinite alternate-reverse}` +
  `.fly{animation:hand 1.2s steps(12) both}` +
  `.star{animation:bang .6s steps(2) infinite alternate}` +
  `.walkin{animation:walk 1.5s steps(10) both}` +
  `.pop{animation:pop .25s steps(3) both}` +
  `@keyframes bob{from{transform:translateY(0)}to{transform:translateY(-4px)}}` +
  `@keyframes bang{from{transform:translateY(0)}to{transform:translateY(-6px)}}` +
  `@keyframes z{0%{opacity:0;transform:translate(0,0)}30%{opacity:1}100%{opacity:0;transform:translate(8px,-14px)}}` +
  `@keyframes walk{from{transform:translateX(-120px)}to{transform:translateX(0)}}` +
  `@keyframes pop{from{opacity:0}to{opacity:1}}`

/** The whole studio floor as one SVG document. */
export function drawFloor(floor: Floor, now: number, selected: RoleId | null): string {
  const helpers = floor.helpers.slice(-COLS)
  const rows = 2 + (helpers.length > 0 ? 1 : 0)
  const width = COLS * CELL_W
  const height = rows * CELL_H
  const draw: Draw = { floor, now, selected }

  let body = `<rect width="${width}" height="${height}" fill="#181a26"/>`
  ROLES.forEach((r, i) => {
    body += station(r.id, r.name, i, draw)
  })
  body += board(floor, ROLES.length)
  helpers.forEach((h, i) => {
    body += helperSpot(h, i, 2 * CELL_H, now)
  })
  body += packageLayer(floor, now)

  return (
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" shape-rendering="crispEdges">` +
    `<style>${CSS}</style>${body}</svg>`
  )
}

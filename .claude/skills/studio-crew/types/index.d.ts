export type RoleId =
  | 'editor'
  | 'transcriber'
  | 'cutter'
  | 'researcher'
  | 'animator'
  | 'sound'
  | 'finisher'

export type Mood = 'idle' | 'working'

export type Worker = {
  mood: Mood
  /** What the speech bubble says while working. */
  line: string
  /** Last few finished jobs, newest last, each led by a tick or a cross. */
  log: string[]
  /** The first `!!` line of the last sound check, when it failed. */
  alert: string | null
}

export type Helper = {
  id: string
  name: string
  line: string
  isDone: boolean
  arrivedAt: number
}

export type Handoff = { from: RoleId; to: RoleId; at: number }

export type Floor = {
  crew: Record<RoleId, Worker>
  /** Who holds the video package right now. */
  holder: RoleId
  handoff: Handoff | null
  helpers: Helper[]
  delivered: number
  deliveredAt: number
  project: string
}

declare module 'claude-code' {
  interface PluginState {
    'studio-crew': {
      floor: Floor
      selected: RoleId | null
      isTrimOn: boolean
    }
  }
}

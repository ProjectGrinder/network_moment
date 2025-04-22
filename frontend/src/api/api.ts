type Listener<T = any> = (payload: T) => void

export class WebSocketManager {
  private socket: WebSocket | null = null
  private listeners: Map<string, Set<Listener>> = new Map()

  connect(url: string) {
    if (this.socket) return

    this.socket = new WebSocket(url)
    console.log(url)

    this.socket.onmessage = (e: MessageEvent) => {
      console.log(e)
      try {
        const { event, data } = JSON.parse(e.data)

        const callbacks = this.listeners.get(event)
        if (callbacks) {
          for (const cb of callbacks) {
            cb(data)
          }
        }
      } catch (err) {
        console.error('Invalid message format', err)
      }
    }
  }

  subscribe<T = any>(eventType: string, callback: Listener<T>) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set())
    }
    this.listeners.get(eventType)!.add(callback as Listener)
  }

  unsubscribe<T = any>(eventType: string, callback: Listener<T>) {
    this.listeners.get(eventType)?.delete(callback as Listener)
  }

  send(event: string, data: any) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ event, data }))
    }
  }
  disconnect() {
    if (this.socket && this.socket.readyState !== WebSocket.CLOSED) {
      console.log('called')
      this.socket.close()
    }

    // Clean up regardless of readyState
    this.socket = null
    this.listeners.clear()
  }
}

export const socketManager = new WebSocketManager()

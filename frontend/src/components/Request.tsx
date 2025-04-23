import React, { useContext } from 'react'
import { WebSocketContext } from './WebSocketProvider'

const Request: React.FC<{ chatname: string }> = ({ chatname }) => {
  const socketManager = useContext(WebSocketContext)
  return (
    <div style={{ textAlign: 'center', marginTop: '20px' }}>
      <p>Please click the button below to requst to join:</p>
      <button
        onClick={() => socketManager?.send('join-chat', { chatname: chatname })}
      >
        Click Here
      </button>
    </div>
  )
}

export default Request

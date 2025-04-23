import { useContext, useState } from 'react'
import ChatMessageBox from './ChatMessageBox'
import { WebSocketContext } from './WebSocketProvider'

interface ChatAreaProps {
  chatname: string
  pfp: number
  admin: Array<any>
  whitelist: Array<any>
  messages: Array<any>
}

function ChatArea({
  chatname,
  pfp,
  admin,
  whitelist,
  messages,
}: ChatAreaProps) {
  const [message, setMessage] = useState('')

  const socketManager = useContext(WebSocketContext)
  let isAdmin = false
  for (const user of admin) {
    if (socketManager.currentUser === user.username) {
      isAdmin = true
      break
    }
  }
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '95vh',
        justifyContent: 'space-between',
      }}
    >
      <h1
        style={{
          margin: 0,
          padding: '10px',
          fontWeight: 'bold',
          fontSize: '25px',
        }}
      >
        {chatname}
      </h1>
      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
          padding: '10px',
        }}
      ></div>
      <h3>Admin</h3>
      <div className="flex flex-wrap flex-row gap-2 p-2 w-full bg-white">
        {admin.map((e) => {
          return <span key={e.username}>{e.username}</span>
        })}
      </div>
      <h3>Members</h3>
      <div className="flex flex-wrap flex-row gap-2 p-2 w-full bg-white">
        {whitelist.map((e) => {
          return isAdmin ? (
            <button
              key={e.username}
              onClick={() => {
                socketManager?.send('add-admin', {
                  chatname: chatname,
                  username: e.username,
                })
              }}
            >
              {e.username}
            </button>
          ) : (
            <span key={e.username}>{e.username}</span>
          )
        })}
      </div>
      <div style={{ flex: 1 }}>
        <div
          style={{
            overflowY: 'scroll',
            padding: '10px',
            flex: 1,
            backgroundColor: '#f9f9f9',
          }}
        >
          {messages.map((message, index) => (
            <ChatMessageBox
              key={index}
              name={message.user.username}
              message={message.message}
              chatname={chatname}
              isAdmin={isAdmin}
            />
          ))}
        </div>
      </div>
      <div
        style={{
          bottom: 0,
          backgroundColor: '#fff',
          padding: '10px',
          borderTop: '1px solid #ccc',
        }}
      >
        <input
          type="text"
          placeholder="Type your message..."
          style={{ width: '100%', padding: '10px' }}
          value={message}
          onChange={(e) => setMessage(e.currentTarget.value)}
        />
        <button
          className="bg-blue-500 text-white rounded-md"
          style={{
            padding: '10px 20px',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
          onClick={(e) => {
            e.preventDefault()
            socketManager?.send('post-message', {
              chatname: chatname,
              message: message,
            })
            setMessage('')
          }}
        >
          Send
        </button>
      </div>
    </div>
  )
}

export default ChatArea

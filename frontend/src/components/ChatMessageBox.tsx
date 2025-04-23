import { useContext } from 'react'
import { WebSocketContext } from './WebSocketProvider'

interface ChatBoxProps {
  name: string
  message: string
  chatname: string
  isAdmin: boolean
}

const ChatBox: React.FC<ChatBoxProps> = ({
  name,
  message,
  chatname,
  isAdmin,
}) => {
  const socketManager = useContext(WebSocketContext)
  const handleClick = () => {
    socketManager?.send('remove-user', { chatname: chatname, username: name })
  }
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'row',
        border: '1px solid #aaa',
        padding: '10px',
        borderRadius: '8px',
        cursor: 'pointer',
        marginBottom: '10px',
        backgroundColor: 'rgba(255, 255, 255, 0.4)',
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
        justifyContent: 'space-between',
      }}
    >
      <div>
        <p
          className="name"
          style={{
            margin: 0,
            paddingLeft: '20px',
            fontSize: '20px',
            fontWeight: 'bold',
            marginBottom: '5px',
          }}
        >
          {name}
        </p>
        <p
          className="message"
          style={{ margin: 0, paddingLeft: '20px', fontSize: '15px' }}
        >
          {message}
        </p>
      </div>
      {isAdmin && (
        <button
          className="bg-red-500 text-white rounded-md"
          style={{
            padding: '10px 20px',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
          onClick={() => handleClick()}
        >
          Kick Member
        </button>
      )}
    </div>
  )
}

export default ChatBox

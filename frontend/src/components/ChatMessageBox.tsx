interface ChatBoxProps {
  name: string
  message: string
}

const ChatBox: React.FC<ChatBoxProps> = ({ name, message }) => {
  return (
    <div
      className="box"
      style={{
        display: 'flex',
        flexDirection: 'column',
        border: '1px solid #aaa',
        padding: '10px',
        borderRadius: '8px',
        cursor: 'pointer',
        marginBottom: '10px',
        backgroundColor: 'rgba(255, 255, 255, 0.4)',
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
      }}
    >
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
  )
}

export default ChatBox

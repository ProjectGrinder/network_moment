import ChatMessageBox from '@/components/ChatMessageBox'
import PrivateChatBox from '@/components/PrivateChatBox'
import GroupChatBox from '@/components/GroupChatBox'

function Chat() {
  return (
    <div className="flex h-screen">
      {/* Left side */}
      <div className="w-1/4 bg-blue-100 p-6 flex flex-col">
        {/* Top section */}
        <div className="flex-1 mb-4 overflow-y-auto-4">
          <h1 className="text-2xl font-bold mb-4">Hello User</h1>
          <h2 className="text-xl font-bold mb-4">Chatroom</h2>
          <button className="bg-blue-500 text-white rounded-md p-2 mb-4 w-full">
            Create Chatroom
          </button>
          <GroupChatBox
            name="Lonely People"
            imageUrl="https://globig.co/wp-content/uploads/2018/11/bigstock-Best-Internet-Concept-of-globa-159909171-1-1080x675.jpg"
            onClick={() => alert('here')}
          />
        </div>
        {/* Bottom section */}
        <div className="flex-1 overflow-y-auto">
          <h2 className="text-xl font-bold mb-4">Inbox</h2>
          {/* <input
            type="text"
            placeholder="User"
            className="border-2 border-gray-300 rounded-md p-2 mb-4 w-full"
          />
          <input
            type="text"
            placeholder="Message"
            className="border-2 border-gray-300 rounded-md p-2 mb-4 w-full"
          />
          <button className="bg-blue-500 text-white rounded-md p-2 mb-4 w-full">
            Send Message
          </button> */}
          <PrivateChatBox
            name="Jane"
            imageUrl="https://i.pinimg.com/736x/cd/df/d1/cddfd18ca77217f324ee9b5b5746278c.jpg"
            onClick={() => alert('SUI')}
          />
          <PrivateChatBox
            name="Jack"
            imageUrl="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQA7zN7F5jvD-unsnN2itVT9x5Q80icFWa27A&s"
            onClick={() => alert(':D')}
          />
        </div>
      </div>
      {/* Right side */}
      <div className="w-3/4 bg-green-100 p-6">
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
            Lonely People
          </h1>
          <div
            style={{
              display: 'flex',
              justifyContent: 'flex-end',
              padding: '10px',
            }}
          >
            <button
              className="bg-red-500 text-white rounded-md"
              style={{
                padding: '10px 20px',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
              onClick={() => alert('Button clicked!')}
            >
              Kick Member
            </button>
          </div>
          <div style={{ flex: 1 }}>
            <ChatMessageBox
              name="Hoshimachi Suisei"
              message="Hello, how are you?"
            />
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
            />
            <button
              className="bg-blue-500 text-white rounded-md"
              style={{
                padding: '10px 20px',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Chat

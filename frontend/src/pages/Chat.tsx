import ChatMessageBox from '@/components/ChatMessageBox'
import PrivateChatBox from '@/components/PrivateChatBox'
import GroupChatBox from '@/components/GroupChatBox'
import UserChatBox from '@/components/UserBox'
import { useContext, useEffect, useState } from 'react'
import {
  useWebSocketEvent,
  WebSocketContext,
} from '@/components/WebSocketProvider'
import Modal from '@/components/Modal'
import ChatArea from '@/components/ChatArea'
import Request from '@/components/Request'
import anime from '../assets/anime.jpg'
import dog from '../assets/dog.jpg'
import gamer from '../assets/gamer.jpg'
import man from '../assets/man.jpg'
import woman from '../assets/woman.jpg'
import { useNavigate } from 'react-router-dom'

const assetImages = [anime, dog, gamer, man, woman]
function Chat() {
  const socketManager = useContext(WebSocketContext)
  const redirect = useNavigate()

  if (!socketManager.currentUser) {
    console.log(socketManager.currentUser)
    window.location.href = "/"
  }

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [userList, setUserList] = useState<any[]>([])
  const [chatList, setChatList] = useState<any[]>([])
  const [user, setUser] = useState('')
  const [message, setMessage] = useState('')
  const [inbox, setInbox] = useState<any[]>([])
  const [request, setRequest] = useState<any | null>(null)
  const [chatroomName, setChatroomName] = useState('')
  const [isPublic, setIsPublic] = useState(false)
  const [selectedImage, setSelectedImage] = useState(0)
  const [displayMessage, setDisplayMessage] = useState<any | null>(null)
  const [isNoAccess, setIsNoAccess] = useState(false)
  const [currentChat, setCurrentChat] = useState('')

  useWebSocketEvent('update-user-list', (data) => {
    setUserList(data)
    console.log(data)
  })

  useWebSocketEvent('update-chat-list', (data) => {
    setChatList(data)
    console.log(data)
  })

  useWebSocketEvent('update-inbox', (data) => {
    setInbox([...inbox, data])
    console.log(data)
  })

  useWebSocketEvent('join-request', (data) => {
    setRequest(data)
    console.log(data)
  })

  useWebSocketEvent('update-chat-detail', (data) => {
    setIsNoAccess(false)
    setDisplayMessage(data)
    console.log(data)
  })

  useWebSocketEvent('revoke-access', (data) => {
    setDisplayMessage(null)
    console.log(data)
  })

  useWebSocketEvent('no-access', (data) => {
    setIsNoAccess(true)
    setDisplayMessage(null)
    console.log(data)
  })

  useWebSocketEvent('resolve-join-request', (data) => {
    setRequest(null)
    setIsNoAccess(false)
    socketManager?.send('open-chat', { chatname: data.chatname })
    console.log(data.chatname)
  })

  useWebSocketEvent('delete-chat', (data) => {
    socketManager?.send('get-data', {})
    if (currentChat == data.chatname) {
      setDisplayMessage(null)
      setCurrentChat('')
    }
  })

  useEffect(() => {
    socketManager?.send('get-data', {})
  }, [])

  const handleCreateChatroom = () => {
    socketManager?.send('create-chat', {
      chatname: chatroomName,
      public: isPublic,
      pfp: selectedImage,
    })
    setIsModalOpen(false)
  }

  const handleJoinChatroom = (username) => {
    socketManager?.send('accept-join-request', {
      chatname: chatroomName,
      username: username,
    })
    setIsModalOpen(false)
  }

  return (
    <>
      <div className="flex h-screen">
        {/* Left side */}
        <div className="w-1/4 bg-blue-100 p-6 flex flex-col">
          {/* Top section */}
          <div className="flex-1 mb-4 overflow-y-auto-4">
            <h1 className="text-2xl font-bold mb-4">
              Hello {socketManager.currentUser}
            </h1>
            <h2 className="text-xl font-bold mb-4">Chatroom</h2>
            <button
              className="bg-blue-500 text-white rounded-md p-2 mb-4 w-full"
              onClick={() => setIsModalOpen(true)}
            >
              Create Chatroom
            </button>
            <ul className="overflow-y-auto max-h-60">
              {chatList.map((chat, index) => (
                <li key={index} className="mb-2">
                  <GroupChatBox
                    name={chat.chatname}
                    imageNum={chat.pfp}
                    isPublic={chat.public}
                    onClick={() => {
                      socketManager?.send('open-chat', {
                        chatname: chat.chatname,
                      })
                      setCurrentChat(chat.chatname)
                    }}
                  />
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h2 className="text-xl font-bold mb-4">User List</h2>
            <ul className="overflow-y-auto max-h-60">
              {userList.map((user, index) => (
                <li key={index} className="mb-2">
                  <UserChatBox name={user.username} imageNum={user.pfp} />
                </li>
              ))}
            </ul>
          </div>
          {/* Bottom section */}
          <div className="flex-1 overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Inbox</h2>
            <input
              type="text"
              placeholder="User"
              className="border-2 border-gray-300 rounded-md p-2 mb-4 w-full"
              value={user}
              onChange={(e) => setUser(e.currentTarget.value)}
            />
            <input
              type="text"
              placeholder="Message"
              className="border-2 border-gray-300 rounded-md p-2 mb-4 w-full"
              value={message}
              onChange={(e) => setMessage(e.currentTarget.value)}
            />
            <button
              className="bg-blue-500 text-white rounded-md p-2 mb-4 w-full"
              onClick={(e) => {
                e.preventDefault()
                socketManager?.send('inbox', {
                  username: user,
                  message: message,
                })
              }}
            >
              Send Message
            </button>
            <ul>
              {inbox.map((user, index) => (
                <li key={index} className="mb-2">
                  <PrivateChatBox
                    name={user.sender.username}
                    imageNum={user.sender.pfp}
                    onClick={() => alert(user.message)}
                  />
                </li>
              ))}
            </ul>
          </div>
        </div>
        {/* Right side */}
        <div className="w-3/4 bg-green-100 p-6">
          {isNoAccess ? (
            <Request chatname={currentChat} />
          ) : (
            displayMessage && <ChatArea {...displayMessage} />
          )}
        </div>
        {/* Modal for creating chatroom */}
      </div>
      {isModalOpen && (
        <Modal onClose={() => setIsModalOpen(false)}>
          <h2 className="text-xl font-bold mb-4">Create Chatroom</h2>
          <input
            type="text"
            placeholder="Chatroom Name"
            className="border-2 border-gray-300 rounded-md p-2 mb-4 w-full"
            value={chatroomName}
            onChange={(e) => setChatroomName(e.target.value)}
          />
          <div className="flex items-center mb-4">
            <label className="mr-2">Public:</label>
            <input
              type="checkbox"
              checked={isPublic}
              onChange={(e) => setIsPublic(e.target.checked)}
            />
          </div>
          <div className="grid grid-cols-3 gap-5">
              {assetImages.map((image, index) => (
                <label key={index} className="flex flex-col items-center">
                  <input
                    type="radio"
                    name="profileImage"
                    value={image}
                    checked={index === selectedImage}
                    className="hidden peer"
                    onClick={() => setSelectedImage(index)}
                    onChange={(e) => {
                      e.currentTarget.checked = index === selectedImage
                    }}
                  />
                  <img
                    src={image}
                    alt={`Profile ${index + 1}`}
                    className="w-20 h-20 object-cover rounded-full border-2 border-gray-300 
                    cursor-pointer hover:border-blue-500 peer-checked:ring-2 peer-checked:ring-blue-500"
                  />
                </label>
              ))}
          </div>
          <button
            className="bg-blue-500 text-white rounded-md p-2 w-full"
            onClick={handleCreateChatroom}
          >
            Create
          </button>
        </Modal>
      )}
      {request && (
        <Modal
          onClose={() => {
            setRequest(null)
          }}
        >
          <h2 className="text-xl font-bold mb-4">Join Request</h2>
          <p>Request from {request.user.username}</p>
          <p>To chatroom {request.chatname}</p>
          <button
            className="bg-blue-500 text-white rounded-md p-2 w-full"
            onClick={() => handleJoinChatroom(request.user.username)}
          >
            Accept
          </button>
        </Modal>
      )}
    </>
  )
}

export default Chat

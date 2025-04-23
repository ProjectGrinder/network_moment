import { useNavigate } from 'react-router-dom'
import anime from '../assets/anime.jpg'
import dog from '../assets/dog.jpg'
import gamer from '../assets/gamer.jpg'
import man from '../assets/man.jpg'
import woman from '../assets/woman.jpg'
import { useContext, useState } from 'react'
import {
  useWebSocketEvent,
  WebSocketContext,
} from '@/components/WebSocketProvider'

function Register() {
  const assetImages = [anime, dog, gamer, man, woman]
  const [selection, changeSelect] = useState(0)
  const [username, changeUsername] = useState('')
  const navigate = useNavigate()
  const socketManager = useContext(WebSocketContext)

  useWebSocketEvent('update-user-list', (data) => {
    socketManager.currentUser = username
    navigate('/chat')
  })

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="bg-white p-6 rounded-md shadow-md w-1/2">
        <h1 className="text-3xl font-bold mb-4 text-center">
          Welcome to MaiMai Message
        </h1>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            if (username.length === 0) return
            socketManager.send('register-user', { username, pfp: selection })
          }}
        >
          <div className="mb-4">
            <label
              htmlFor="username"
              className="block text-gray-700 font-bold mb-2"
            >
              Username
            </label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => changeUsername(e.currentTarget.value)}
              required
              placeholder="Enter your username"
              className="border-2 border-gray-300 rounded-md p-2 w-full"
            />
          </div>
          <div className="mb-4">
            <label
              htmlFor="profileImage"
              className="block text-gray-700 font-bold mb-2"
            >
              Profile Image
            </label>
            <div className="grid grid-cols-3 gap-4">
              {assetImages.map((image, index) => (
                <label key={index} className="flex flex-col items-center">
                  <input
                    type="radio"
                    name="profileImage"
                    value={image}
                    checked={index === selection}
                    className="hidden peer"
                    onClick={() => changeSelect(index)}
                    onChange={(e) => {
                      e.currentTarget.checked = index === selection
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
          </div>
          <button
            type="submit"
            className="bg-blue-500 text-white rounded-md p-2 w-full"
          >
            Login
          </button>
        </form>
      </div>
    </div>
  )
}

export default Register

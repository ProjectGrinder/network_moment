import anime from '../assets/anime.jpg'
import dog from '../assets/dog.jpg'
import gamer from '../assets/gamer.jpg'
import man from '../assets/man.jpg'
import woman from '../assets/woman.jpg'

const images = [anime, dog, gamer, man, woman]

interface UserChatBoxProps {
  name: string
  imageNum: number
}

const UserChatBox: React.FC<UserChatBoxProps> = ({ name, imageNum }) => {
  return (
    <div
      className="box"
      style={{
        display: 'flex',
        alignItems: 'center',
        border: '1px solid #aaa',
        padding: '10px',
        borderRadius: '8px',
        cursor: 'pointer',
        marginBottom: '10px',
        backgroundColor: 'rgba(255, 255, 255, 0.4)',
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
      }}
    >
      <img
        src={images[imageNum]}
        alt={name}
        className="image"
        style={{
          width: '50px',
          height: '50px',
          borderRadius: '50%',
          objectFit: 'cover',
        }}
      />
      <p
        className="name"
        style={{ margin: 0, paddingLeft: '20px', fontSize: '20px' }}
      >
        {name}
      </p>
    </div>
  )
}

export default UserChatBox

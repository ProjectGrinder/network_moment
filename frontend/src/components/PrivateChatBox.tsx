interface PrivateChatBoxProps {
  name: string
  imageUrl: string
  onClick: () => void
}

const PrivateChatBox: React.FC<PrivateChatBoxProps> = ({
  name,
  imageUrl,
  onClick,
}) => {
  return (
    <div
      className="box"
      onClick={onClick}
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
        src={imageUrl}
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

export default PrivateChatBox

import React from 'react'

interface ModalProps {
  children: React.ReactNode
  onClose: () => void
}

const Modal: React.FC<ModalProps> = ({ children, onClose }) => {
  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-10 flex items-center justify-center"
      onClick={onClose}
    >
      <div
        className="bg-white p-6 rounded-md shadow-md"
        onClick={(e) => e.stopPropagation()}
      >
        {children}
        <button
          className="mt-4 bg-red-500 text-white rounded-md p-2"
          onClick={onClose}
        >
          Close
        </button>
      </div>
    </div>
  )
}

export default Modal

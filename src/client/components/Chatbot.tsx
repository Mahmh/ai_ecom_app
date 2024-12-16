import Image from 'next/image'
import ReactMarkdown from 'react-markdown';
import { useState, useEffect, useContext } from 'react'
import { AppContext } from '@/helpers/context'
import { isLoggedIn, Request } from '@/helpers/utils'
import { Message, MessageToSend } from '@/helpers/interfaces'
import chatIcon from '@icons/chat.png'

export default function Chatbot() {
    const { account, conversation, setConversation } = useContext(AppContext)
    const [isShown, setIsShown] = useState(false)
    const [messageToSend, setMessageToSend] = useState<MessageToSend>({ sender: '', content: '', conversation: [] })
    const [waitingForResponse, setWaitingForResponse] = useState(false)

    const addMessageToConversation = (newMessage: Message) => {
        setConversation((prevConversation) => [...prevConversation, newMessage])
    }

    const sendMessage = async () => {
        console.log(conversation)
        const userMessage: MessageToSend = {
            sender: messageToSend.sender,
            content: messageToSend.content,
            conversation: conversation
        }

        addMessageToConversation({ sender: userMessage.sender, content: userMessage.content })
        setMessageToSend(prev => ({ ...prev, content: '' }))
        setWaitingForResponse(true)

        await new Request(
            `chatbot`,
            (AIResponse: Message) => {
                addMessageToConversation(AIResponse)
                setWaitingForResponse(false)
            },
            userMessage
        ).post()
    }

    useEffect(() => {
        if (isLoggedIn(account)) setMessageToSend(prev => ({ ...prev, sender: account.username }))
    }, [account])

    return (
        <>
            <div id="chatbot-content" className={isShown ? 'show' : ''}>
                <section id='chatbot-header'>
                    <h1>AI Assistant</h1>
                    <button onClick={() => setIsShown(false)}>⨯</button>
                </section>
                <section id="chat-content">
                    {conversation.length > 0 ? conversation.map((msg: Message, i) => (
                        <div key={i} className={msg.sender !== 'chatbot' ? 'user-message' : 'chatbot-message'}>
                            <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                    )) : <p id='chat-init-msg'>Type & send your questions to our helpful customer support chatbot!</p>}
                </section>
                <section id='chat-tools'>
                    <input
                        placeholder='Type your message here'
                        value={messageToSend.content}
                        onChange={e => setMessageToSend((prev) => ({ ...prev, content: e.target.value }))}
                        maxLength={100}
                    />
                    <button onClick={sendMessage} disabled={waitingForResponse || !messageToSend.content.trim()}>
                        {waitingForResponse ? 'Waiting...' : 'Send'}
                    </button>
                </section>
            </div>
            {!isShown && (
                <button id="chatbot-content-btn" onClick={() => setIsShown(true)}>
                    <Image src={chatIcon} alt='Chat' width={75} height={50} priority={true}/>
                </button>
            )}
        </>
    )
}

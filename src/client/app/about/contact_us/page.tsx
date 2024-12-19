'use client'
import { useState, useRef } from 'react'
import { Page } from '@/helpers/components'
import { SubmitMessage, Status } from '@/helpers/interfaces'

export default function ContactUsPage() {
    const [email, setEmail] = useState('')
    const [feedback, setFeedback] = useState('')
    const [submitMsg, setSubmitMsg] = useState<SubmitMessage>({ msg: '', status: Status.Pending })
    const emailRef = useRef<HTMLInputElement|null>(null)
    const feedbackRef = useRef<HTMLTextAreaElement|null>(null)

    const validateEmail = (email: string): boolean => {
        const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
        return re.test(String(email).toLowerCase())
    }

    const handleSubmit = () => {
        if (validateEmail(email)) {
            if (feedback.length > 0 && emailRef.current && feedbackRef.current) {
                emailRef.current.value = ''
                feedbackRef.current.value = ''
                setEmail('')
                setFeedback('')
                setSubmitMsg({ msg: 'Thank you for contacting us! We will respond to you shortly via e-mail.', status: Status.Success })
            } else setSubmitMsg({ msg: 'Sorry, but you must include a feedback.', status: Status.Failure })
        } else setSubmitMsg({ msg: 'Sorry, but you have included an invalid email.', status: Status.Failure })
    }

    return (
        <Page id='contact-us-content'>
            <h1>Contact Us</h1>
            <div>
                <input placeholder='Type your E-mail' onChange={e => setEmail(e.target.value)} ref={emailRef}/>
                <textarea placeholder='Type your feedback, suggestion, or business inquiry' onChange={e => setFeedback(e.target.value)} ref={feedbackRef}/>
                <button onClick={handleSubmit}>Submit</button>
                <label id={submitMsg.status === Status.Success ? `success-submit-msg` : `failure-submit-msg`}>{submitMsg.msg}</label>
            </div>
        </Page>
    )
}
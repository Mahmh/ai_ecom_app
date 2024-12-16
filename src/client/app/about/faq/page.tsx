'use client'
import { Page } from '@/helpers/components'
import FAQ from '@data/faq.json'

export default function FAQPage() {
    return (
        <Page id='faq-content'>
            {FAQ.map((row: { answer: string, question: string }, i) => (
                <div key={i}>
                    <h1 style={{ marginBottom: 0 }}>{row.question}</h1>
                    <p>{row.answer}</p>
                </div>
            ))}
        </Page>
    )
}
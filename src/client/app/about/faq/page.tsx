'use client'
import { Page } from '@helpers/components'
import FAQ from '@data/faq.json'

export default function About() {
    return (
        <Page id='about-content'>
            {FAQ.map((row: { answer: string, question: string }, i: number) => (
                <div key={i}>
                    <h1 style={{ marginBottom: 0 }}>{row.question}</h1>
                    <p>{row.answer}</p>
                </div>
            ))}
        </Page>
    )
}
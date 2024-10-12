'use client'
import { Page } from '@/helpers/components'
import { TopRatedProducts } from './page'

export default function NotFound() {
    return (
        <Page id='not-found-content'>
            <section id='not-found-sec'>
                <h1>404 Not Found</h1>
                <p>The page you we're looking for doesn't exist, but here are some products you might like:</p>
            </section>
            <TopRatedProducts/>
        </Page>
    )
}
import { AboutLinkProps } from '@/helpers/interfaces'
import Link from 'next/link'

const CategoryLink = ({ category }: { category: string }) => <Link href={`/products?category=${category}`}>{category}</Link>
const AboutLink = ({ section, children }: AboutLinkProps) => (
    <Link href={`/about/${section.toLowerCase().replace(' ', '_')}`}>
        {section}{children}
    </Link>
)

export const CategoryLinks = () => (
    <section className='category-links'>
        <CategoryLink category='Electronics'/>
        <CategoryLink category='Clothes'/>
        <CategoryLink category='Accessories'/>
        <CategoryLink category='Furniture'/>
    </section>
)

export const AboutLinks = ({ desc=false }) => (
    <section className='about-links'>
        <AboutLink section='FAQ'>{desc && <><br/><p>Frequently asked questions about EcomGo.</p></>}</AboutLink>
        <AboutLink section='Contact Us'>{desc && <><br/><p>Do you need help or do you want to send a feedback? Don't hesitate to contact us!</p></>}</AboutLink>
    </section>
)

export default function Footer() {
    return (
        <footer>
            <section>
                <h2>Categories</h2>
                <CategoryLinks/>
            </section>
            <section>
                <h2>About</h2>
                <AboutLinks desc={false}/>
                <p>Copyright © 2024 EcomGo. All rights reserved.</p>
            </section>
        </footer>
    )
}
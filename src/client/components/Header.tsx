import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState, useEffect, useContext, ReactNode, ChangeEvent, KeyboardEvent } from 'react'
import { NavLink } from '@helpers/components'
import { CategoryLinks, AboutLinks } from '@components/Footer'
import { AppContext } from '@/helpers/context'
import { HeaderNavLinkProps, TooltipProps } from '@/helpers/interfaces'

// Related
const Search = () => {
    const [searchInput, setSearchInput] = useState('')
    const router = useRouter()
    const handleEnter = (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') { e.preventDefault(); router.push(`/products?search_query=${searchInput}`) }
    }
    const handleInput = (e: ChangeEvent<HTMLInputElement>) => { e.preventDefault(); setSearchInput(e.target.value) }
    return <input placeholder='Search' maxLength={30} onChange={handleInput} onKeyDown={handleEnter}/>
}


const HeaderNavLink = ({ children, href, setHovered, setLastHovered }: HeaderNavLinkProps) => (
    <NavLink 
        href={href.toLowerCase()} 
        onMouseOver={() => { setHovered(children); setLastHovered(children) }} 
        onMouseOut={() => setHovered('')}
    >{children}</NavLink>
)


const Tooltip = ({ constHeaderBgcolor, hovered, setHovered, lastHovered, contents, content_names }: TooltipProps) => (
    <div 
        className={`tooltip-container ${constHeaderBgcolor ? 'scrolled' : ''}`} 
        style={hovered ? { opacity: 1, visibility: 'visible' } : { transition: 'all 250ms ease 300ms' }}
        onMouseOver={() => setHovered('Tooltip')} 
        onMouseOut={() => setHovered('')}
    >
        <div className={`tooltip-arrow ${constHeaderBgcolor ? 'scrolled-arrow' : ''}`}></div>
        {contents.map((content, i) => (lastHovered === content_names[i] ?
            <div key={i} id={`${content_names[i].toLowerCase()}-tooltip`}>{content}</div> 
        : null))}
    </div>
)


// Tooltip contents
const ProductTooltip = () => {
    const { topRated } = useContext(AppContext)
    return (
        <>
            <section>
                <h1>Categories</h1>
                <CategoryLinks/>
            </section>
            <section>
                <h1>Top Rated</h1>
                {topRated.slice(3, 5).map((product, i) => 
                    <Link key={i} href={`/products?product_id=${product['product_id']}`}>
                        {product['name']}<br/>
                        <p>{product['description']}</p>
                    </Link>
                )}
            </section>
        </>
    )
}


const AboutTooltip = () => (
    <>
        <h1>Sections</h1>
        <AboutLinks desc={true}/>
    </>
)


// Main
export default function Header({ constHeaderBgcolor=false }) {
    const [scrolled, setScrolled] = useState(false)
    const [hovered, setHovered] = useState<string|ReactNode>('')
    const [lastHovered, setLastHovered] = useState<string|ReactNode>('')
    const headerNavLinks = ['Products', 'About']
    const { account } = useContext(AppContext)

    useEffect(() => {
        // Scroll handling
        if (typeof window !== 'undefined') window.scrollTo({ top: 0 });
        const handleScroll = () => setScrolled(window.scrollY > 150)
        window.addEventListener('scroll', handleScroll)
        return () => window.removeEventListener('scroll', handleScroll)
    }, [])

    return (
        <>
            <header className={scrolled || constHeaderBgcolor ? 'scrolled' : ''}>
                <h1><Link href='/'>EcomGo</Link></h1>
                <nav>
                    <HeaderNavLink href='/products' setHovered={setHovered} setLastHovered={setLastHovered}>{headerNavLinks[0]}</HeaderNavLink>
                    <HeaderNavLink href='/about/faq' setHovered={setHovered} setLastHovered={setLastHovered}>{headerNavLinks[1]}</HeaderNavLink>
                    <Search/>
                    {
                        account.username 
                        ? <Link href={'/account'} id='login-btn'>{account.username}</Link> 
                        : <Link href={'/account/login'} id='login-btn'>Log in</Link>
                    }
                </nav>
            </header>
            <Tooltip 
                constHeaderBgcolor={scrolled || constHeaderBgcolor} 
                hovered={hovered} 
                setHovered={setHovered}
                lastHovered={lastHovered}
                content_names={headerNavLinks}
                contents={[<ProductTooltip/>, <AboutTooltip/>]}
            />
        </>
    )
}
import { useState, useEffect, useRef, useContext, MouseEvent } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { NavLinkProps, PageProps, ProductObject, DropdownProps, PaginationControlsProps, Account } from '@helpers/interfaces'
import { isLoggedIn, Request, round } from '@helpers/utils'
import { AppContext } from '@helpers/context'
import Image from 'next/image'
import Header from '@components/Header'
import Footer from '@components/Footer'
import Link from 'next/link'


export const NavLink = ({ href, exact = false, children, ...props }: NavLinkProps) => {
    const pathname = usePathname()
    const isActive = exact ? pathname === href : pathname.startsWith(href)
    const className = `${props.className || ''} ${isActive ? 'active' : ''}`.trim()
    return <Link href={href} {...props} className={className}>{children}</Link>
}


export const Page = ({ children, id, constHeaderBgcolor=true }: PageProps) => (
    <>
        <Header constHeaderBgcolor={constHeaderBgcolor}/>
        <main id={id}>{children}</main>
        <Footer/>
    </>
)


export const ProductCard = ({ product }: { product: ProductObject }) => {
    const [inCart, setInCart] = useState(false)
    const { product_id, name, description, image_file, discount } = product
    const { account, setAccount } = useContext(AppContext)
    const price = round(product.price, 2)
    const discounted_price = round(price - (discount*price), 2)
    const router = useRouter()

    /** Adds this product to the logged-in user's cart */
    const addToCart = (e: MouseEvent<HTMLButtonElement>) => {
        e.stopPropagation()
        if (isLoggedIn(account)) {
            let new_cart = account.cart || []
            if (inCart) {
                new_cart = new_cart.filter(product => product.product_id !== product_id)
                setInCart(false)
            } else {
                new_cart.push(product)
                setInCart(true)
            }
            setAccount({ ...account, cart: new_cart })
        } else {
            router.push('/account/login')
        }
    }

    useEffect(() => {
        if (account.cart) setInCart(account.cart.filter(product => product.product_id === product_id).length === 1)
    }, [inCart])
    
    return (
        <div className='product-card'>
            <Link href={`/products?product_id=${product_id}`}>
                <div>
                    <Image src={`http://localhost:8000/product_images/${image_file}`} alt={name ? name : 'product'} width={250} height={250} priority={true}/>
                    <article>
                        <h1 className='product-name'>{name}</h1>
                        <label className='product-description'>{description}</label>
                    </article>
                </div>
                <div>
                    <h3>
                        {discount ?
                            <>
                                <span className='old-price'>${price}</span>
                                <span>${discounted_price}</span>
                            </>  : <span>${price}</span>
                        }
                    </h3>
                </div>
            </Link>
            <button className={inCart ? 'remove-from-cart-btn' : 'add-to-cart-btn'} onClick={addToCart}>
                {inCart ? 'Remove from cart' : 'Add to Cart'}
            </button>
        </div>
    )
}


export const Dropdown = ({ options, selectedOption, setSelectedOption }: DropdownProps) => {
    const [isOpen, setIsOpen] = useState(false)
    const dropdownRef = useRef<HTMLDivElement|null>(null)

    useEffect(() => {
        const handleClickOutside = (e: Event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) setIsOpen(false)
        }
        document.addEventListener('mousedown', handleClickOutside)
        return () => { document.removeEventListener('mousedown', handleClickOutside) }
    }, [])

    return (
        <div className='dropdown' ref={dropdownRef}>
            <button onClick={() => setIsOpen(!isOpen)} className='dropdown-toggle'>
                {selectedOption}
            </button>
            <ul className={`dropdown-menu ${isOpen ? 'open' : ''}`}>
                {options.map((option: string, i: number) => (
                    <li
                        key={i}
                        onClick={() => { setSelectedOption(option); setIsOpen(false) }}
                        className={`dropdown-item ${option === selectedOption ? 'selected-dropdown-item' : ''}`}
                    >
                        {option}
                    </li>
                ))}
            </ul>
        </div>
    )
}


export const PaginationControls = ({ items, setShownItems, reloadFactors }: PaginationControlsProps) => {
    const [currentPage, setCurrentPage] = useState(1)
    const items_per_page = items.length >= 10 ? 10 : items.length
    const pages = round(items.length / items_per_page)

    useEffect(() => { setCurrentPage(1) }, reloadFactors)
    useEffect(() => {
        const start = (currentPage-1) * items_per_page
        const end = start + items_per_page
        setShownItems(items.slice(start, end))
    }, [currentPage, items])

    return items.length > 0 && (
        <section id='pagination-controls'>
            <label>Page: </label>
            <div>
                {Array.from({length: pages}, (_, i) => i+1).map(page_idx => (
                    <button 
                        key={page_idx} 
                        onClick={() => setCurrentPage(page_idx)}
                        className={page_idx === currentPage ? 'active-page-btn' : ''}
                    >{page_idx}</button>
                ))}
            </div>
        </section>
    )
}


export const AccountSignedOutPage = ({ section }: { section: 'Log in' | 'Sign up' }) => {
    const is_login = section === 'Log in'
    const short_section = is_login ? 'login' : 'signup'
    const inverse_section = is_login ? 'Sign up' : 'Log in'
    const inverse_short_section = is_login ? 'signup' : 'login'
    const [inputUsername, setInputUsername] = useState('')
    const [inputPassword, setInputPassword] = useState('')
    const [errMsg, setErrMsg] = useState('')
    const { setAccount } = useContext(AppContext)
    const router = useRouter()

    const checkCredentials = (account: Account) => {
        if (typeof account !== 'string') {
            console.log('account', account)
            setAccount({ ...account, username: inputUsername, password: inputPassword })
            router.push('/account')
        } else {
            setErrMsg(is_login ? 
                'Either your inputted credentials are incorrect or the account does not exist.' : 
                'This username is already taken. Please use another one.'
            )
        }
    }

    const handleClick = async () => {
        if (inputUsername.length < 3) { setErrMsg('Username must contain at least 3 characters.'); return }
        if (inputPassword.length < 3) { setErrMsg('Password must contain at least 3 characters.'); return }
        const endpoint = is_login ? 'log_in_account' : 'create_account'
        const data = { username: inputUsername, password: inputPassword }
        await new Request(endpoint, checkCredentials, data).post()
    }

    return (
        <Page id={`${short_section}-content`}>
            <section>
                <div id='credentials-banner'></div>
                <div>
                    <input placeholder='Username' onChange={e => setInputUsername(e.target.value)}/>
                    <input placeholder='Password' onChange={e => setInputPassword(e.target.value)} type='password'/>
                    <button onClick={handleClick}>{section}</button>
                    <label id='err-msg'>{errMsg}</label>
                </div>
            </section>
            <p>
                {is_login ? 'No account created yet?' : 'Already have an account?'}
                <Link href={`/account/${inverse_short_section}`}> {inverse_section}</Link>.
            </p>
        </Page>
    )
}
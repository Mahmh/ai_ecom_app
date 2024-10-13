import { useState, useEffect, useRef, useContext, MouseEvent } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { NavLinkProps, PageProps, ProductObject, DropdownProps, PaginationControlsProps, Account, UserObject } from '@/helpers/interfaces'
import { Request, addToCart, removeFromCart, getDiscountedPrice, isLoggedIn, isProductInCart, round } from '@/helpers/utils'
import { AppContext } from '@/helpers/context'
import Image from 'next/image'
import Header from '@/components/Header'
import Footer from '@/components/Footer'
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


export const CartButton = ({ product }: { product: ProductObject }) => {
    const [inCart, setInCart] = useState(false)
    const { account, setAccount } = useContext(AppContext)
    const { product_id } = product
    const router = useRouter()

    const handleCart = async (e: MouseEvent<HTMLButtonElement>) => {
        e.stopPropagation()
        if (isLoggedIn(account)) {
            let new_cart: ProductObject[]
            if (isProductInCart(product_id, account)) {
                new_cart = await removeFromCart(product, account)
                setInCart(false)
            } else {
                new_cart = await addToCart(product, account)
                setInCart(true)
            } 
            setAccount({ ...account, cart: new_cart })
        } else {
            router.push('/account/login')
        }
    }

    useEffect(() => {
        setInCart(isProductInCart(product_id, account))
    }, [inCart, account.cart, product])

    return (
        <button className={inCart ? 'remove-from-cart-btn' : 'add-to-cart-btn'} onClick={handleCart}>
            {inCart ? 'Remove from cart' : 'Add to Cart'}
        </button>
    )
}


export const ProductCard = ({ product, isLoading }: { product?: ProductObject, isLoading?: boolean }) => {
    if (isLoading || !product) {
        return (
            <div className='product-card loading-product-card'>
                <a>
                    <div>
                        <div className='loading-img'></div>
                        <article>
                            <h1 className='product-name'></h1>
                            <label className='product-description'></label>
                        </article>
                    </div>
                    <div>
                        <h3>
                            <span className='price'>$xxx</span>
                        </h3>
                    </div>
                </a>
                <button></button>
            </div>
        )
    } else {
        const { product_id, name, description, image_file, price, discount } = product
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
                                    <span className='price'>${getDiscountedPrice(price, discount)}</span>
                                </>  : <span className='price'>${price}</span>
                            }
                        </h3>
                    </div>
                </Link>
                <CartButton product={product}/>
            </div>
        )
    }
}


export const UserCard = ({ user, isLoading }: { user?: UserObject, isLoading?: boolean }) => {
    return isLoading || !user ? (
        <div className='user-card loading-user-card'>
            <a><h1></h1><p></p></a>
        </div>
    ) : (
        <div className='user-card'>
            <Link href={`/users?username=${user.username.replace('&', '[amps]')}`}>
                <h1>{user.username}</h1>
                <p>{user.bio ? user.bio : <i>[No bio provided]</i>}</p>
            </Link>
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


export const LoggedOutPage = ({ section }: { section: 'Log in' | 'Sign up' }) => {
    const is_login = section === 'Log in'
    const short_section = is_login ? 'login' : 'signup'
    const inverse_section = is_login ? 'Sign up' : 'Log in'
    const inverse_short_section = is_login ? 'signup' : 'login'
    const [inputUsername, setInputUsername] = useState('')
    const [inputPassword, setInputPassword] = useState('')
    const [errMsg, setErrMsg] = useState('')
    const { setAccount } = useContext(AppContext)
    const router = useRouter()

    const getInputCredentials = () => ({ username: inputUsername, password: inputPassword })

    const checkCredentials = async (response: Account|string) => {
        if (typeof response !== 'string') {
            await new Request('get_cart', (cart: ProductObject[]) =>  { 
                setAccount({ username: inputUsername, password: inputPassword, bio: response.bio, cart: cart })
            }, getInputCredentials()).post()
            router.push('/account')
        } else {
            setErrMsg(
                is_login
                ? 'Either your inputted credentials are incorrect or the account does not exist.' 
                : 'This username is already taken. Please use another one.'
            )
        }
    }

    const submit = async () => {
        if (inputUsername.length < 3) { setErrMsg('Username must contain at least 3 characters.'); return }
        if (inputPassword.length < 3) { setErrMsg('Password must contain at least 3 characters.'); return }
        const endpoint = is_login ? 'log_in_account' : 'create_account'
        await new Request(endpoint, checkCredentials, getInputCredentials()).post()
    }

    return (
        <Page id={`${short_section}-content`}>
            <section>
                <div id='credentials-banner'></div>
                <div>
                    <input placeholder='Username' onChange={e => setInputUsername(e.target.value)}/>
                    <input placeholder='Password' onChange={e => setInputPassword(e.target.value)} type='password'/>
                    <button onClick={submit}>{section}</button>
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
'use client'
import { AppContext, nullAccount } from '@/helpers/context'
import { useContext, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Page, ProductCard } from '@/helpers/components'
import { ProductObject } from '@/helpers/interfaces'
import { Request, getDiscountedPrice, isLoggedIn, getCredentials } from '@/helpers/utils'
import Link from 'next/link'

export default function Account() {
    const [total, setTotal] = useState(0)
    const [isEditingBio, setIsEditingBio] = useState(false)
    const [newBio, setNewBio] = useState('')
    const [productDisplay, setProductDisplay] = useState<'row'|'column'>('row')
    const { account, setAccount } = useContext(AppContext)
    const router = useRouter()

    const logOut = () => {
        setAccount(nullAccount)
        router.push('/account/login')
    }

    const deleteAccount = async () => {
        await new Request('delete_account', logOut, getCredentials(account)).delete()
    }

    const editBio = async () => {
        if (isEditingBio) {
            if (newBio.length > 0) {
                await new Request(
                    'edit_bio', 
                    () => { setAccount({ ...account, bio: newBio }); setIsEditingBio(false) },
                    { ...getCredentials(account), new_bio: newBio }
                ).patch()
            } else {
                setIsEditingBio(false)
            }
        } else {
            setIsEditingBio(true)
        }
    }

    useEffect(() => {
        if (isLoggedIn(account)) {
            if (account.cart) {
                let newTotal = 0
                for (const product of account.cart) newTotal += getDiscountedPrice(product.price, product.discount);
                setTotal(newTotal)
            }
        } else {
            logOut()
        }
    }, [account])
    
    return (
        <Page id='account-content'>
            <div>
                <section id='account-details'>
                    <h1>{account.username}</h1>
                    <p>{
                        isEditingBio 
                        ? <input id='new-bio-input' placeholder='Type your new bio' onChange={e => setNewBio(e.target.value)}/>
                        : (account.bio ? account.bio : <i>[No bio provided]</i>)
                    }</p>
                    <div>
                        <button id='edit-bio-btn' onClick={editBio}>{isEditingBio ? 'Confirm' : 'Edit bio'}</button>
                        <button id='logout-btn' onClick={logOut}>Log out</button>
                        <button id='delete-account-btn' onClick={deleteAccount}>Delete account</button>
                    </div>
                </section>
                <section id='account-cart'>
                    <div id='my-cart-div'>
                        <h1>My Cart</h1>
                        <div>
                            <button 
                                onClick={() => setProductDisplay('row')} 
                                style={{ marginRight: 10 }}
                                className={productDisplay === 'row' ? 'active-display' : ''}
                            >Row</button>
                            <button 
                                onClick={() => setProductDisplay('column')}
                                className={productDisplay === 'column' ? 'active-display' : ''}
                            >Column</button>
                        </div>
                    </div>
                    <div className={`product-container ${productDisplay && account.cart?.length > 0 ? `${productDisplay}-display` : ''}`}>
                        {
                            account.cart?.length > 0
                            ? account.cart.map((product: ProductObject, i) => <ProductCard product={product} key={i}/>)
                            : <p>No items in cart. <Link href='/' id='shopping-link'>Start shopping!</Link></p>
                        }
                    </div>
                </section>
            </div>
            <div id='checkout-details'>
                <h2>Checkout Details</h2>
                {
                    account.cart?.length > 0
                    ? <>
                        <ol>
                            {account.cart.map((product: ProductObject, i) => (
                                <li key={i}>{product.name} (${getDiscountedPrice(product.price, product.discount)})</li>
                            ))}
                        </ol>
                        <p>Total: ${total}</p>
                    </>
                    : <p>Details will available once you have added a product to your cart.</p>
                }
            </div>
        </Page>
    )
}
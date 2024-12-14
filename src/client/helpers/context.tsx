'use client'
import { createContext, useState, useEffect } from 'react'
import { ParentProps, ContextProps, ProductObject, Account, UserObject } from '@/helpers/interfaces'
import { Request } from '@/helpers/utils'

export const nullAccount: Account = { username: '', password: '', bio: '', cart: [] }
export const nullProduct: ProductObject = { product_id: -1, name: '', description: '', image_file: '', price: 0, discount: 0, owner: '', category: '' }
export const nullUser: UserObject = { username: '', bio: '', owned_products: [] }

export const AppContext = createContext<ContextProps>({
    account: nullAccount,
    setAccount: () => {},
    topRated: [],
    setTopRated: () => {},
    isTopRatedLoading: true
})

export function AppProvider({ children }: ParentProps) {
    const [account, setAccount] = useState<Account>(nullAccount)
    const [topRated, setTopRated] = useState<ProductObject[]>([])
    const [isTopRatedLoading, setIsTopRatedLoading] = useState(true)
    
    useEffect(() => {
        const num_topRated = 5
        setIsTopRatedLoading(true);
        (async () => await new Request(`get_most_rated_products?k=${num_topRated}`, setTopRated).get())()
        setIsTopRatedLoading(false)
    }, [])

    return (
        <AppContext.Provider value={{
            account, setAccount,
            topRated, setTopRated,
            isTopRatedLoading
        }}>{children}</AppContext.Provider>
    )
}
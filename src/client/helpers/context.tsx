'use client'
import { createContext, useState, useEffect } from 'react'
import { ParentProps, ContextProps, ProductObject, Account } from '@helpers/interfaces'
import { Request } from '@helpers/utils'

export const nullAccount: Account = { username: '', password: '', bio: '', cart: [] }
export const AppContext = createContext<ContextProps>({
    account: nullAccount,
    setAccount: () => {},
    topRated: [],
    setTopRated: () => {}
})

export function AppProvider({ children }: ParentProps) {
    const [account, setAccount] = useState<Account>(nullAccount)
    const [topRated, setTopRated] = useState<ProductObject[]>([])
    
    useEffect(() => {
        const num_topRated = 5;
        (async () => await new Request(`get_most_rated_products?k=${num_topRated}`, setTopRated).get())()
    }, [])

    return (
        <AppContext.Provider value={{
            account, setAccount,
            topRated, setTopRated
        }}>{children}</AppContext.Provider>
    )
}
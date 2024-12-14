'use client'
import { useState, useEffect } from 'react'
import { Page, PaginationControls, ProductCard, UserCard } from '@/helpers/components'
import { Request } from '@/helpers/utils'
import { nullUser } from '@/helpers/context'
import { UserObject, UserSearchParams } from '@/helpers/interfaces'
import { useSearchParams } from 'next/navigation'
import NotFound from '../not-found'

const User = ({ username }: { username: string }) => {
    const [user, setUser] = useState<UserObject>(nullUser)
    const [found, setFound] = useState(true)

    const getUserInfo = (user: UserObject) => {
        if (typeof user !== 'string') setUser(user)
        else setFound(false)
    }
    
    useEffect(() => {
        if (typeof window !== 'undefined') window.scrollTo({ top: 0 });
        (async () => await new Request(`get_user_info?username=${username}`, getUserInfo).get())()
    }, [username])

    return found ? (
        <Page id='user-content'>
            <section>
                <h1>{user.username}</h1>
                <p>{user.bio ? user.bio : <i>[No bio provided]</i>}</p>
            </section>
            <section>
                <h1>Owned Products</h1>
                <div className='product-container'>
                    {
                        user.owned_products?.length > 0 
                        ? user.owned_products.map(p => <ProductCard key={p.product_id} product={p}/>) 
                        : <p className='no-results-msg'>No results.</p>
                    }
                </div>
            </section>
        </Page>
    ) : <NotFound/>
}


const Catalog = (searchParams: UserSearchParams) => {
    const [users, setUsers] = useState<UserObject[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState('')
    const [shownUsers, setShownUsers] = useState<UserObject[]>([])

    // Function to get the most relevant users
    const getUsers = async () => {
        await new Request(
            searchQuery.length > 0 ? `search_users?search_query=${searchQuery}` : 'get_all_users', 
            setUsers
        ).get()
        setIsLoading(false)
    }

    useEffect(() => { if (typeof window !== 'undefined') window.scrollTo({ top: 0 }) }, [])
    useEffect(() => { if (searchParams.search_query) setSearchQuery(searchParams.search_query) }, [searchParams.search_query])
    useEffect(() => { getUsers() }, [searchParams.search_query, searchQuery])

    return (
        <Page id='user-catalog'>
            <section id='user-search-tools'>
                <input placeholder='Type here to search' value={searchQuery ? searchQuery : ''} onChange={e => setSearchQuery(e.target.value)}/>
            </section>
            <section className='user-container'>
                {
                    isLoading 
                    ? Array.from({ length: 5 }, (_, i) => <UserCard key={i} isLoading={isLoading}/>)
                    : shownUsers.length > 0 
                       ? shownUsers.map(user => <UserCard key={user.username} user={user}/>) 
                       : <p className='no-results-msg'>No results.</p>
                }
            </section>
            {!isLoading && <PaginationControls items={users} setShownItems={setShownUsers} reloadFactors={[searchQuery]}/>}
        </Page>
    )
}


export default function UsersPage() {
    const searchParams = useSearchParams()
    const username = searchParams.get('username') || ''
    const search_query = searchParams.get('search_query') || ''
    return username ? <User username={username}/> : <Catalog search_query={search_query}/> 
}
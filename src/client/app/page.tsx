'use client'
import { useContext, useEffect, useState } from 'react'
import { Page, ProductCard } from '@/helpers/components'
import { AppContext } from '@/helpers/context'
import { isLoggedIn, Request } from '@/helpers/utils'
import { ProductObject } from '@/helpers/interfaces'

// Related
const Banner = () => (
    <section id='banner'>
        <div id='slogan'>
            <h1>World's Top Digital Marketplace</h1>
            <p>Your AI-powered e-commerce platform.</p>
        </div>
    </section>
)


export const TopRatedProducts = () => {
    const { topRated, isTopRatedLoading } = useContext(AppContext)
    return (
        <section id='top-rated-products-sec'>
            <h1>Top Rated</h1>
            <div className='product-container'>
                {
                    isTopRatedLoading 
                    ? Array.from({ length: 5 }, (_, i) => <ProductCard key={i} isLoading={isTopRatedLoading}/>)
                    : topRated && topRated.map((product, i) => <ProductCard key={i} product={product} isLoading={isTopRatedLoading}/>)
                }
            </div>
        </section>
    )
}

const DiscoverProducts = () => {
    const [products, setProducts] = useState<ProductObject[]>([])
    const [isLoading, setIsLoading] = useState(true)

    const getProducts = (all_products: ProductObject[]) => {
        setProducts(all_products.slice(10, 20))
        setIsLoading(false)
    }

    useEffect(() => {
        setIsLoading(true);
        (async () => await new Request('get_all_products', getProducts).get())()
    }, [])

    return (
        <section id='discover-products-sec'>
            <h1>Discover</h1>
            <div className='product-container'>
                {
                    isLoading 
                    ? Array.from({ length: 5 }, (_, i) => <ProductCard key={i} isLoading={isLoading}/>)
                    : products && products.map((product, i) => <ProductCard key={i} product={product} isLoading={isLoading}/>)
                }
            </div>
        </section>
    )
}


const Recommended = () => {
    const { account } = useContext(AppContext)
    const [isLoading, setIsLoading] = useState(true)
    const [products, setProducts] = useState<ProductObject[]>([])

    const getRecommendedProducts = async () => {
        if (!isLoggedIn(account)) return
        setIsLoading(true)
        await new Request(
            `recommender?username=${account.username}`,
            (response: ProductObject[]) => {
                setProducts(response)
                setIsLoading(false)
            }
        ).get()
    }

    useEffect(() => { getRecommendedProducts() }, [])

    return isLoggedIn(account) && products.length > 0 && (
        <section id='recommended-sec'>
            <h1>Recommended</h1>
            <div className='product-container'>
                {products.map((p, i) => <ProductCard key={i} product={p} isLoading={isLoading}/>)}
            </div>
        </section>
    )
}


// Main
export default function MainPage() {
    return (
        <Page constHeaderBgcolor={false}>
            <Banner/>
            <Recommended/>
            <TopRatedProducts/>
            <DiscoverProducts/>
        </Page>
    )
}
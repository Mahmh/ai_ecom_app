'use client'
import { useContext, useEffect, useState } from 'react'
import { Page, ProductCard } from '@/helpers/components'
import { AppContext } from '@/helpers/context'
import { isLoggedIn, Request } from '@/helpers/utils'
import { ContextProps, ProductObject } from '@/helpers/interfaces'

// Related
const Banner = () => (
    <section id='banner'>
        <div id='slogan'>
            <h1>World's Top Digital Marketplace</h1>
            <p>Shop Smart, Shop Fast, Shop EcomGo!</p>
        </div>
    </section>
)


const TopRatedProducts = () => {
    const { topRated } = useContext(AppContext)
    return (
        <section id='top-rated-products-sec'>
            <h1>Top Rated</h1>
            <div className='product-container'>
                {topRated && topRated.map((product: ProductObject, i: number) => <ProductCard key={i} product={product}/>)}
            </div>
        </section>
    )
}

const DiscoverProducts = () => {
    const [products, setProducts] = useState<ProductObject[]>([])

    useEffect(() => {
        const handleProducts = (all_products: ProductObject[]) => {
            setProducts(all_products.slice(10, 20))
        }
        (async () => await new Request(`get_all_products`, handleProducts).get())();
    }, [])

    return (
        <section id='discover-products-sec'>
            <h1>Discover</h1>
            <div className='product-container'>
                {products && products.map((product, i) => <ProductCard key={i} product={product}/>)}
            </div>
        </section>
    )
}


const Recommended = () => {
    const { account } = useContext(AppContext)
    return isLoggedIn(account) && (
        <section id='recommended-sec'>
            <h1>Recommended</h1>
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
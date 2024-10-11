'use client'
import { useState, useEffect } from 'react'
import Image from 'next/image'
import { Page, ProductCard, Dropdown, PaginationControls, CartButton } from '@/helpers/components'
import { getDiscountedPrice, Request } from '@/helpers/utils'
import { ProductObject, ProductSearchParams } from '@/helpers/interfaces'
import { nullProduct } from '@/helpers/context'

const Product = ({ product_id }: { product_id: number }) => {
    const [product, setProduct] = useState<ProductObject>(nullProduct)
    const [reviews, setReviews] = useState([])
    
    useEffect(() => {
        if (typeof window !== 'undefined') window.scrollTo({ top: 0 });
        (async () => await new Request(`get_product_using_id?product_id=${product_id}`, setProduct).get())();
        (async () => await new Request(`get_reviews_of_product?product_id=${product_id}`, setReviews).get())();
    }, [product_id])

    return (
        <Page id='product-content'>
            <section id='product'>
                {
                    product.image_file &&
                    <Image 
                        src={`http://localhost:8000/product_images/${product.image_file}`} 
                        alt={product.name ? product.name : 'product'} 
                        width={550} height={550} priority={true}
                    />
                }
                <div id='product-properties'>
                    <h1 className='product-name'>{product.name}</h1>
                    <p className='product-owner'>{product.owner}</p>
                    <p className='product-description'>{product.description}</p>
                    <h3 id='price'>
                        {product.discount ?
                            <>
                                <span className='old-price'>${product.price}</span>
                                <span>${getDiscountedPrice(product.price, product.discount)}</span>
                            </>  : <span>${product.price}</span>
                        }
                    </h3>
                    <CartButton product={product}/>
                </div>
            </section>
            <div className='horizontal-sep'></div>
            <section id='reviews'>
                {reviews.map((review, i) => (
                    <div key={i}>
                        <h3>{review[0]}</h3>
                        <p>{review[1]}</p>
                    </div>
                ))}
            </section>
        </Page>
    )
}





const Catalog = (searchParams: ProductSearchParams) => {
    const [products, setProducts] = useState<ProductObject[]>([])
    const categories = ['All', 'Electronics', 'Clothes', 'Accessories', 'Furniture']
    const [category, setCategory] = useState(categories[0])
    const [searchQuery, setSearchQuery] = useState('')
    const [shownProducts, setShownProducts] = useState<ProductObject[]>([])

    // Function to get the most relevant products
    const getProducts = async () => {
        let all_products = await new Request(`get_all_products`).get()
        const filterByCategory = (products: ProductObject[]) => products.filter(product => product.category.toLowerCase() === category.toLowerCase())
        
        if (category === categories[0] && searchQuery.length === 0) {
            setProducts(all_products); return
        }

        if (category && category !== categories[0]) {
            all_products = filterByCategory(all_products)
            if (searchQuery.length === 0) setProducts(all_products)
        }

        if (searchQuery.length > 0) {
            const candidates: ProductObject[] = await new Request(`search_products?search_query=${searchQuery}`).get()
            if (category && category !== categories[0]) { setProducts(filterByCategory(candidates)); return }
            setProducts(candidates)
        }
    }

    useEffect(() => { if (typeof window !== 'undefined') window.scrollTo({ top: 0 }) }, [])
    useEffect(() => { if (searchParams.search_query) setSearchQuery(searchParams.search_query) }, [searchParams.search_query])
    useEffect(() => { if (searchParams.category && categories.includes(searchParams.category)) setCategory(searchParams.category) }, [searchParams.category])
    useEffect(() => { getProducts() }, [searchParams.category, searchParams.search_query, category, searchQuery])

    return (
        <Page id='product-catalog'>
            <section id='product-search-tools'>
                <input placeholder='Type here to search' value={searchQuery ? searchQuery : ''} onChange={e => setSearchQuery(e.target.value)}/>
                <Dropdown 
                    options={categories} 
                    selectedOption={category} 
                    setSelectedOption={setCategory}
                />
            </section>
            <section className='product-container'>
                {
                    shownProducts.length > 0 
                    ? shownProducts.map(product => <ProductCard key={product.product_id} product={product}/>) 
                    : <p className='no-results-msg'>No results.</p>
                }
            </section>
            <PaginationControls items={products} setShownItems={setShownProducts} reloadFactors={[category, searchQuery]}/>
        </Page>
    )
}


export default function ProductsPage({ searchParams }: { searchParams: ProductSearchParams }) {
    const { product_id, category, search_query } = searchParams
    return product_id ? <Product product_id={product_id}/> : <Catalog category={category} search_query={search_query}/> 
}
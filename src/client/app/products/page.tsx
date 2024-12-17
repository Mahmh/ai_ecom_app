'use client'
import Image from 'next/image'
import Link from 'next/link'
import { useState, useEffect, useContext } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Page, ProductCard, Dropdown, PaginationControls, CartButton } from '@/helpers/components'
import { getCredentials, getDiscountedPrice, isLoggedIn, Request, sentimentToInt } from '@/helpers/utils'
import { Sentiment, ProductObject, ProductSearchParams, Review } from '@/helpers/interfaces'
import { AppContext, nullProduct } from '@/helpers/context'
import NotFound from '../not-found'
import ratedIcon from '@icons/rated.png'
import unratedIcon from '@icons/unrated.png'

const Product = ({ product_id }: { product_id: number }) => {
    const router = useRouter()
    const { account } = useContext(AppContext)
    const [product, setProduct] = useState<ProductObject>(nullProduct)
    const [found, setFound] = useState(true)
    const [rated, setRated] = useState(false)
    const [reviews, setReviews] = useState<Review[]>([])
    const [filteredReviews, setFilteredReviews] = useState<Review[]>([])
    const [selectedSentiment, setSelectedSentiment] = useState<Sentiment>('all')
    const [sentimentCounts, setSentimentCounts] = useState([0,0,0,0])
    const [isAddReviewDivShown, setIsAddReviewDivShown] = useState(false)
    const [updateReviewInputIdx, setUpdateReviewInputIdx] = useState(-1)
    const [reviewToAdd, setReviewToAdd] = useState('')
    const [reviewToUpdate, setReviewToUpdate] = useState('')
    const sentiments = ['All', 'Positive', 'Neutral', 'Negative']

    const getProductInfo = async () => (
        await new Request(`get_product_using_id?product_id=${product_id}`, (product: ProductObject) => {
            typeof product !== 'string' ? setProduct(product) : setFound(false)
        }).get()
    )

    const loadReviews = async () => (
        await new Request(`get_reviews_of_product?product_id=${product_id}`, (reviews: Review[] | string) => {
            if (typeof reviews == 'string') { console.error(reviews); return }
            setSentimentCounts([
                reviews.length,
                reviews.filter(review => review.sentiment === sentimentToInt('positive')).length,
                reviews.filter(review => review.sentiment === sentimentToInt('neutral')).length,
                reviews.filter(review => review.sentiment === sentimentToInt('negative')).length
            ])
            setReviews(reviews)
        }).get()
    )

    const addReview = async () => {
        if (isLoggedIn(account)) {
            await new Request(
                `add_product_review?product_id=${product.product_id}&review=${reviewToAdd}`,
                loadReviews,
                getCredentials(account)
            ).patch()
            setIsAddReviewDivShown(false)
        } else router.push('/account/login')
    }

    const deleteReview = (reviewIdx: number) => (
        async () => {
            if (isLoggedIn(account)) {
                await new Request(
                    `remove_product_review?product_id=${product.product_id}&review_idx=${reviewIdx}`,
                    loadReviews,
                    getCredentials(account)
                ).delete()
            } else router.push('/account/login')
        }
    )

    const editReview = (reviewIdx: number) => (
        async () => {
            if (isLoggedIn(account)) {
                await new Request(
                    `update_product_review?product_id=${product.product_id}&review_idx=${reviewIdx}&new_review=${reviewToUpdate}`,
                    loadReviews,
                    getCredentials(account)
                ).patch()
                setUpdateReviewInputIdx(-1)
            } else router.push('/account/login')
        }
    )

    const rateOrUnrateProduct = async () => {
        if (isLoggedIn(account)) {
            await new Request(
                `${rated ? 'unrate_product' : 'rate_product'}?product_id=${product.product_id}`,
                x=>x,
                getCredentials(account)
            ).patch()
            setRated(!rated)
            getUserRating()
        } else router.push('/account/login')
    }

    const getUserRating = async () => {
        if (!isLoggedIn(account)) return
        await new Request(
            `get_raters_of_product?product_id=${product_id}`,
            (raters: string[]) => setRated(raters.includes(account.username))
        ).get()
    }

    useEffect(() => {
        if (typeof window !== 'undefined') window.scrollTo({ top: 0 })
        getProductInfo()
        getUserRating()
        loadReviews()
    }, [product_id])

    useEffect(() => {
        // Filter reviews based on selected sentiment
        setFilteredReviews(
            selectedSentiment != 'all'
            ? reviews.filter(review => review.sentiment === sentimentToInt(selectedSentiment))
            : reviews
        )
    }, [reviews, selectedSentiment])

    return found ? (
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
                    <h1 className='product-name'>
                        {product.name}
                        <button onClick={rateOrUnrateProduct} id='rate-btn' className={rated ? 'rated' : ''}>
                            <Image src={rated ? ratedIcon : unratedIcon} alt={'Rate product'} width={40} height={40} priority={true}/>
                        </button>
                    </h1>
                    <Link href={`/users?username=${product.owner.replace('&', '[amps]')}`} className='product-owner'>{product.owner}</Link>
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

            <section className='horizontal-sep-sec'>
                <div className='horizontal-sep-upper'>
                    <h1>
                        Reviews
                        <button onClick={() => setIsAddReviewDivShown(isAddReviewDivShown ? false : true)}>
                            {isAddReviewDivShown ? '⨯' : '+'}
                        </button>
                    </h1>
                    <div>
                        {sentiments.map((sentiment: string, i) => (
                            <button
                                className={sentiment.toLowerCase() === selectedSentiment ? 'selected-sentiment' : ''}
                                onClick={() => setSelectedSentiment(sentiment.toLowerCase() as Sentiment)}
                                key={i}
                            >{sentiment} ({sentimentCounts[i]})</button>
                        ))}
                    </div>
                </div>
                <div className='horizontal-sep-line'></div>
            </section>

            <section id='reviews'>
                <div id='add-review-div' style={isAddReviewDivShown ? {} : { display: 'none' }}>
                    <textarea onChange={e => setReviewToAdd(e.target.value)}/>
                    <button onClick={addReview}>Add Review</button>
                </div>
                {filteredReviews.length > 0 ? filteredReviews.map((review: Review, i) => (
                    <div className={review.sentiment === 1 ? 'positive-review' : review.sentiment === -1 ? 'negative-review' : ''} key={i}>
                        <section>
                            <Link href={`/users?username=${review.username}`}>
                                {review.username} {review.username === account.username ? '(You)' : ''}
                            </Link>
                            {
                                updateReviewInputIdx === i 
                                ? <textarea onChange={e => setReviewToUpdate(e.target.value)}/>
                                : <p>{review.review}</p>
                            }
                        </section>
                        <section>
                            {review.username === account.username && <>
                                <button
                                    onClick={
                                        updateReviewInputIdx === i
                                        ? editReview(review.reviewIdx)
                                        : () => setUpdateReviewInputIdx(i)
                                    }
                                >{updateReviewInputIdx === i ? 'Confirm' : 'Edit'}</button>
                                <button onClick={deleteReview(review.reviewIdx)}>Delete</button>
                            </>}
                        </section>
                    </div>
                )) : selectedSentiment != 'all' ? `No reviews with ${selectedSentiment} sentiment.` : 'No reviews available.'}
            </section>
        </Page>
    ) : <NotFound/>
}


const Catalog = (searchParams: ProductSearchParams) => {
    const [products, setProducts] = useState<ProductObject[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const categories = ['All', 'Electronics', 'Clothes', 'Accessories', 'Furniture']
    const [category, setCategory] = useState(categories[0])
    const [searchQuery, setSearchQuery] = useState('')
    const [shownProducts, setShownProducts] = useState<ProductObject[]>([])

    /** Retrieves the most relevant products */
    const getProducts = async () => {
        let all_products = await new Request(`get_all_products`).get()
        const filterByCategory = (products: ProductObject[]) => products.filter(product => product.category.toLowerCase() === category.toLowerCase())
        
        if (category === categories[0] && searchQuery.length === 0) {
            setProducts(all_products)
            return
        }

        if (category && category !== categories[0]) {
            all_products = filterByCategory(all_products)
            if (searchQuery.length === 0) setProducts(all_products)
        }

        if (searchQuery.length > 0) {
            const candidates: ProductObject[] = await new Request(`search_products?search_query=${searchQuery}`).get()
            category && category !== categories[0]
            ? setProducts(filterByCategory(candidates))
            : setProducts(candidates)
        }
    }

    useEffect(() => { if (typeof window !== 'undefined') window.scrollTo({ top: 0 }) }, [])
    useEffect(() => { if (searchParams.search_query) setSearchQuery(searchParams.search_query) }, [searchParams.search_query])
    useEffect(() => { if (searchParams.category && categories.includes(searchParams.category)) setCategory(searchParams.category) }, [searchParams.category])
    useEffect(() => { setIsLoading(true); getProducts(); setIsLoading(false) }, [searchParams.category, searchParams.search_query, category, searchQuery])

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
                    isLoading 
                    ? Array.from({ length: 5 }, (_, i) => <ProductCard key={i} isLoading={isLoading}/>)
                    : shownProducts.length > 0 
                      ? shownProducts.map(product => <ProductCard key={product.product_id} product={product}/>) 
                      : <p className='no-results-msg'>No results.</p>
                }
            </section>
            {!isLoading && <PaginationControls items={products} setShownItems={setShownProducts} reloadFactors={[category, searchQuery]}/>}
        </Page>
    )
}


export default function ProductsPage() {
    const searchParams = useSearchParams()
    const product_id = searchParams.get('product_id') || ''
    const category = searchParams.get('category') || ''
    const search_query = searchParams.get('search_query') || ''
    return product_id ? <Product product_id={Number(product_id)}/> : <Catalog category={category} search_query={search_query}/> 
}
import { ReactNode, SetStateAction, Dispatch } from 'react'

type SetState<T> = Dispatch<SetStateAction<T>>

export interface Metadata {
    readonly title: string
    readonly description: string
}

export interface ProductObject {
    readonly product_id: number
    readonly name: string
    readonly description: string
    readonly image_file: string
    readonly price: number
    readonly discount: number
    readonly owner: string
    readonly category: string
}

export interface ProductSearchParams {
    readonly product_id?: number
    readonly category: string
    readonly search_query: string
}


//// Props ////
// General
export interface ParentProps {
    readonly children: ReactNode
}

export interface ContextProps {
    account: Account
    setAccount: SetState<Account>
    topRated: ProductObject[],
    setTopRated: SetState<ProductObject[]>
    isTopRatedLoading: boolean
}


// Footer
export interface AboutLinkProps extends ParentProps {
    readonly section: string
}


// Header
export interface HeaderNavLinkProps extends ParentProps  {
    href: string
    setHovered: SetState<string|ReactNode>
    setLastHovered: SetState<string|ReactNode>
}

export interface TooltipProps {
    constHeaderBgcolor: boolean
    hovered: string|ReactNode
    setHovered: SetState<string|ReactNode>
    lastHovered: string|ReactNode
    contents: JSX.Element[]
    content_names: string[]
}


// Components
export interface NavLinkProps extends ParentProps {
    readonly href: string
    readonly exact?: boolean
    [key: string]: any // Allow any additional props (...props)
}

export interface PageProps extends ParentProps {
    readonly id?: string
    readonly header?: boolean
    readonly constHeaderBgcolor?: boolean 
}

export interface DropdownProps {
    readonly options: string[]
    selectedOption: string
    setSelectedOption: SetState<string>
}

export interface PaginationControlsProps {
    readonly items: any[]
    setShownItems: SetState<any>
    readonly reloadFactors: any[]
}

export interface Review {
    readonly username: string
    readonly review: string
}

export interface Account {
    username: string
    password: string
    bio: string
    cart: ProductObject[]
}

export interface UserObject {
    username: string
    bio: string
    owned_products: ProductObject[]
}

export interface UserSearchParams {
    readonly username?: string
    readonly search_query: string
}
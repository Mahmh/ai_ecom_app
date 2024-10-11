import { Account } from "@helpers/interfaces"

/**
 * Rounds a given number to a given amount of decimal places
 * @param n The number
 * @param decimal_places How many decimal places to round the number to (default: rounds to the nearest integer)
 * @returns The rounded number
 */
export const round = (n: number, decimal_places: number = 0): number => {
    decimal_places *= 10
    return decimal_places === 0 ? Math.round(n) : Math.round((n + Number.EPSILON) * decimal_places) / decimal_places
}


/**
 * Checks if a user is logged in
 * @param account Account set in the context of the app
 * @returns A boolean indicating if a user is logged in
 */
export const isLoggedIn = (account: Account): boolean => {
    return account.username.length >= 3 && account.password.length >= 3
}


/**
 * Class for making a GET, POST, PATCH, or DELETE request to the API server
 * ### Constructor
 * @param endpoint The API endpoint to send the request
 * @param callbackFunc The callback function to apply to the retrieved JSON response
 * @param data The data payload to send to the API endpoint
 */
export class Request {
    //// Properties ////
    private readonly url: string
    private readonly data: object
    private readonly callbackFunc: (x:any)=>any
    
    constructor(endpoint: string, callbackFunc:(x:any)=>any = x=>x, data: object = {}) {
        this.url = `http://localhost:8000/${endpoint}`
        this.data = data
        this.callbackFunc = callbackFunc
    }
    
    /**
     * Makes `this.data` able to be sent to the API server
     * @param method REST API Method
     * @returns The appropriate payload for the method
     */
    private getPayload(method: string): object {
        return {
            method: method,
            body: JSON.stringify(this.data),
            headers: {'Content-Type': 'application/json'}
        }
    }

    //// Request methods ////
    /**
     * Performs a GET request
     * @returns The output of the inputted callback function
     */
    public async get(): Promise<any> {
        const response = await fetch(this.url)
        return this.callbackFunc(await response.json())
    }

    /**
     * Performs a POST request
     * @returns The output of the inputted callback function
     */
    public async post(): Promise<any> {
        const response = await fetch(this.url, this.getPayload('POST'))
        return this.callbackFunc(await response.json())
    }

    /**
     * Performs a PATCH request
     * @returns The output of the inputted callback function
     */
    public async patch(): Promise<any> {
        const response = await fetch(this.url, this.getPayload('PATCH'))
        return this.callbackFunc(await response.json())
    }

    /**
     * Performs a DELETE request
     * @returns The output of the inputted callback function
     */
    public async delete(): Promise<any> {
        const response = await fetch(this.url, this.getPayload('DELETE'))
        return this.callbackFunc(await response.json())
    }
}
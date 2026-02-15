# Stripe Payment Integration - API Documentation

## Overview

This API provides Stripe payment integration for subscription packages. Users can create checkout sessions by providing a package ID and authentication token, then receive a payment link to complete the purchase.

## Prerequisites

1. **Stripe Account**: Sign up at [stripe.com](https://stripe.com)
2. **API Keys**: Get your keys from [Stripe Dashboard](https://dashboard.stripe.com/apikeys)
3. **Environment Variables**: Add to your `.env` file:

```env
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here  # Optional
FRONTEND_URL=http://localhost:3000
```

## API Endpoints

### 1. Create Checkout Session

Create a Stripe checkout session for a subscription plan.

**Endpoint:** `POST /api/payment/create-checkout`

**Authentication:** Required (Bearer Token)

**Request Body:**
```json
{
  "plan_id": 1
}
```

**Response (200 OK):**
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_...",
  "session_id": "cs_test_..."
}
```

**Example using cURL:**
```bash
curl -X POST http://localhost:8000/api/payment/create-checkout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan_id": 1}'
```

**Example using Python:**
```python
import requests

headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN",
    "Content-Type": "application/json"
}

data = {"plan_id": 1}

response = requests.post(
    "http://localhost:8000/api/payment/create-checkout",
    headers=headers,
    json=data
)

checkout_data = response.json()
print(f"Payment URL: {checkout_data['checkout_url']}")
```

### 2. Webhook Handler

Handles Stripe webhook events (called by Stripe, not by your application).

**Endpoint:** `POST /api/payment/webhook`

**Authentication:** None (verified by Stripe signature)

**Headers:**
- `stripe-signature`: Stripe signature for verification

This endpoint is automatically called by Stripe when payment events occur.

### 3. Payment Success

Callback endpoint after successful payment.

**Endpoint:** `GET /api/payment/success?session_id={SESSION_ID}`

**Authentication:** None

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Payment completed successfully",
  "subscription": {
    "id": 1,
    "plan_id": 1,
    "status": "active",
    "payment_status": "completed",
    "start_date": "2026-02-16T04:00:00Z",
    "end_date": "2026-03-18T04:00:00Z"
  }
}
```

### 4. Payment Cancel

Callback endpoint when payment is cancelled.

**Endpoint:** `GET /api/payment/cancel`

**Authentication:** None

**Response (200 OK):**
```json
{
  "status": "cancelled",
  "message": "Payment was cancelled. You can try again anytime."
}
```

## Payment Flow

1. **User Authentication**: User logs in and receives an access token
2. **Create Checkout**: User's app calls `/api/payment/create-checkout` with plan ID
3. **Redirect to Stripe**: User is redirected to the `checkout_url`
4. **Payment**: User completes payment on Stripe's secure page
5. **Webhook**: Stripe sends webhook to `/api/payment/webhook` (updates subscription)
6. **Redirect Back**: User is redirected to success/cancel URL
7. **Verify**: App can call `/api/payment/success` to verify payment status

## Testing with Stripe Test Mode

### Test Card Numbers

- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **Requires Authentication**: `4000 0025 0000 3155`

**Expiry:** Any future date (e.g., 12/34)  
**CVC:** Any 3 digits (e.g., 123)  
**ZIP:** Any 5 digits (e.g., 12345)

### Testing Webhooks Locally

1. Install Stripe CLI:
```bash
stripe login
```

2. Forward webhooks to your local server:
```bash
stripe listen --forward-to localhost:8000/api/payment/webhook
```

3. Copy the webhook signing secret and add to `.env`:
```env
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Database Schema

The integration adds the following fields to `UserSubscription`:

- `stripe_session_id`: Stripe checkout session ID
- `stripe_payment_intent_id`: Stripe payment intent ID
- `payment_status`: Payment status (pending, completed, failed)

## Error Handling

**401 Unauthorized**: Invalid or missing authentication token
```json
{
  "detail": "Not authenticated"
}
```

**404 Not Found**: Subscription plan not found
```json
{
  "detail": "Subscription plan not found or inactive"
}
```

**400 Bad Request**: Stripe error
```json
{
  "detail": "Stripe error: <error message>"
}
```

## Security Notes

1. **Never expose your secret key** in client-side code
2. **Use HTTPS** in production
3. **Verify webhook signatures** (automatically handled)
4. **Use test keys** during development (keys starting with `sk_test_`)
5. **Rotate keys** if compromised

## Production Checklist

- [ ] Replace test API keys with live keys
- [ ] Update `FRONTEND_URL` to production domain
- [ ] Configure webhook endpoint in Stripe Dashboard
- [ ] Enable HTTPS
- [ ] Test with real payment methods
- [ ] Set up proper error monitoring
- [ ] Review Stripe Dashboard for payment analytics

## Support

For Stripe-specific issues, refer to:
- [Stripe Documentation](https://stripe.com/docs)
- [Stripe API Reference](https://stripe.com/docs/api)
- [Stripe Testing Guide](https://stripe.com/docs/testing)

// Initialize Stripe
const stripe = Stripe('{{ stripe_public_key }}');
const elements = stripe.elements();

// Create card element
const card = elements.create('card');
card.mount('#card-element');

// Handle form submission
const form = document.getElementById('payment-form');
const submitButton = document.getElementById('submit-payment');

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    submitButton.disabled = true;

    try {
        // Create payment intent
        const response = await fetch('/create-payment/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // Confirm payment
        const result = await stripe.confirmCardPayment(data.clientSecret, {
            payment_method: {
                card: card,
                billing_details: {
                    name: document.getElementById('cardholder-name').value,
                },
            },
        });

        if (result.error) {
            // Handle payment error
            window.location.href = `/payment/failure/?error=${result.error.message}`;
        } else {
            // Handle successful payment
            if (result.paymentIntent.status === 'succeeded') {
                window.location.href = '/payment/success/';
            } else if (result.paymentIntent.status === 'requires_action') {
                window.location.href = '/payment/pending/';
            }
        }
    } catch (error) {
        console.error('Payment error:', error);
        window.location.href = `/payment/failure/?error=${error.message}`;
    } finally {
        submitButton.disabled = false;
    }
});

// Handle refund
async function handleRefund(paymentIntentId) {
    try {
        const response = await fetch('/refund/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                payment_intent: paymentIntentId,
            }),
        });
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        window.location.href = '/payment/refund_success/';
    } catch (error) {
        console.error('Refund error:', error);
        window.location.href = `/payment/refund_failure/?error=${error.message}`;
    }
}

// Handle refund cancellation
async function handleRefundCancel(paymentIntentId) {
    try {
        const response = await fetch('/refund-cancel/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                payment_intent: paymentIntentId,
            }),
        });
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        window.location.href = '/payment/refund_cancel_success/';
    } catch (error) {
        console.error('Refund cancellation error:', error);
        window.location.href = `/payment/refund_cancel_failure/?error=${error.message}`;
    }
} 
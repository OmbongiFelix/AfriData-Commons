let currentPackage = {};

function purchaseTokens(packageType, tokens, amount) {
    currentPackage = {
        type: packageType,
        tokens: tokens,
        amount: amount
    };

    const packageNames = {
        'basic': 'Basic Package',
        'standard': 'Standard Package',
        'premium': 'Premium Package',
        'mega': 'Mega Package'
    };

    document.getElementById('packageTitle').textContent = packageNames[packageType];
    document.getElementById('packageDetails').textContent = `${tokens} Tokens for KES ${amount.toLocaleString()}`;
    document.getElementById('amount').value = amount;
    document.getElementById('tokens').value = tokens;
    document.getElementById('package').value = packageType;

    new bootstrap.Modal(document.getElementById('mpesaModal')).show();
}

document.getElementById('mpesaForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const form = this;
    const formData = new FormData(form);
    const phone = formData.get('phone');

    // Validate phone number
    if (!/^[0-9]{9}$/.test(phone)) {
        alert('Please enter a valid 9-digit phone number');
        return;
    }

    // Add 254 prefix
    formData.set('phone', '254' + phone);

    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

    // Get STK URL from form attribute
    const stkUrl = form.getAttribute('data-stk-url');

    fetch(stkUrl, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        bootstrap.Modal.getInstance(document.getElementById('mpesaModal')).hide();

        if (data.success) {
            new bootstrap.Modal(document.getElementById('successModal')).show();
        } else {
            alert('Payment initiation failed: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-mobile-alt"></i> Pay with M-Pesa';
    });
});

// Optional auto-refresh logic
setInterval(() => {
    // You can implement a check for payment status here
}, 30000);

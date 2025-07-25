document.getElementById('paymentForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const phone = document.getElementById('phone').value;
            const amount = document.getElementById('amount').value;
            
            // Validate phone number
            if (!/^[0-9]{9}$/.test(phone)) {
                alert('Please enter a valid 9-digit phone number');
                return;
            }
            
            // Validate amount
            if (amount < 1) {
                alert('Please enter a valid amount');
                return;
            }
            
            // Show loading modal
            new bootstrap.Modal(document.getElementById('loadingModal')).show();
            
            // Prepare form data
            const formData = new FormData(this);
            formData.set('phone', '254' + phone); // Add country code
            
            // Submit the form
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                // Hide loading modal
                bootstrap.Modal.getInstance(document.getElementById('loadingModal')).hide();
                
                if (data.success) {
                    new bootstrap.Modal(document.getElementById('successModal')).show();
                } else {
                    document.getElementById('errorMessage').textContent = data.message || 'Payment failed. Please try again.';
                    new bootstrap.Modal(document.getElementById('errorModal')).show();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                bootstrap.Modal.getInstance(document.getElementById('loadingModal')).hide();
                document.getElementById('errorMessage').textContent = 'Network error. Please check your connection and try again.';
                new bootstrap.Modal(document.getElementById('errorModal')).show();
            });
        });

        // Format phone number input
        document.getElementById('phone').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, ''); // Remove non-digits
            if (value.length > 9) {
                value = value.slice(0, 9);
            }
            e.target.value = value;
        });

        // Format amount input
        document.getElementById('amount').addEventListener('input', function(e) {
            let value = e.target.value.replace(/[^0-9.]/g, ''); // Allow only numbers and decimal
            e.target.value = value;
        });
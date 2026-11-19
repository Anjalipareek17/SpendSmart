/**
 * SpendSmart - Modern Personal Finance & Budget Tracker
 * Interactive client-side scripts: Dynamic Category Switching, Chart.js Visualizations (with ₹ INR formatting),
 * Budget alert helpers, and Modal handling.
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Initialize Category Switcher in Transaction Modal
  initTransactionTypeToggle();

  // 2. Initialize Charts on Dashboard and Reports pages
  initCharts();

  // 3. Auto-dismiss Flash Alerts
  initAlertDismissal();

  // 4. Set today's date in any empty date fields
  initDateDefaults();
});

/**
 * Handles switching between 'Income' and 'Expense' in the Add Transaction modal/form,
 * updating the categories dropdown dynamically.
 */
function initTransactionTypeToggle() {
  const expenseBtn = document.getElementById('typeBtnExpense');
  const incomeBtn = document.getElementById('typeBtnIncome');
  const typeInput = document.getElementById('transactionTypeInput');
  const categorySelect = document.getElementById('categorySelect');

  const expenseCategories = [
    'Food',
    'Travel',
    'Shopping',
    'Bills',
    'Education',
    'Entertainment',
    'Healthcare',
    'Other'
  ];

  const incomeCategories = [
    'Salary',
    'Allowance',
    'Freelancing',
    'Business',
    'Other'
  ];

  if (!expenseBtn || !incomeBtn || !typeInput || !categorySelect) return;

  function setTransactionType(type) {
    typeInput.value = type;

    if (type === 'Expense') {
      expenseBtn.classList.add('active', 'expense');
      incomeBtn.classList.remove('active', 'income');

      populateCategories(expenseCategories);
    } else {
      incomeBtn.classList.add('active', 'income');
      expenseBtn.classList.remove('active', 'expense');

      populateCategories(incomeCategories);
    }
  }

  function populateCategories(cats) {
    categorySelect.innerHTML = '<option value="" disabled selected>Select category...</option>';
    cats.forEach(function (cat) {
      const opt = document.createElement('option');
      opt.value = cat;
      opt.textContent = cat;
      categorySelect.appendChild(opt);
    });
  }

  expenseBtn.addEventListener('click', function () {
    setTransactionType('Expense');
  });

  incomeBtn.addEventListener('click', function () {
    setTransactionType('Income');
  });

  // Default to Expense
  setTransactionType(typeInput.value || 'Expense');
}

/**
 * Initializes and renders Chart.js charts by fetching dynamic JSON from /api/charts
 */
function initCharts() {
  const doughnutCanvas = document.getElementById('expenseChart');
  const barCanvas = document.getElementById('incomeExpenseChart');

  if (!doughnutCanvas && !barCanvas) return;

  // Retrieve optional month/year filter from data attributes if present
  const targetMonth = doughnutCanvas?.dataset.month || '';
  const targetYear = doughnutCanvas?.dataset.year || '';
  const queryParam = (targetMonth && targetYear) ? `?month=${targetMonth}&year=${targetYear}` : '';

  fetch(`/api/charts${queryParam}`)
    .then(response => {
      if (!response.ok) throw new Error('Network response was not ok');
      return response.json();
    })
    .then(data => {
      // 1. Doughnut Chart: Expense Breakdown
      if (doughnutCanvas) {
        renderExpenseDoughnut(doughnutCanvas, data.doughnut);
      }

      // 2. Bar Chart: Income vs Expense Comparison
      if (barCanvas) {
        renderIncomeExpenseBar(barCanvas, data.bar);
      }
    })
    .catch(error => {
      console.warn('Charts failed to load dynamic API data:', error);
    });
}

/**
 * Render Expense Doughnut Chart using Chart.js with Indian Rupee (₹) tooltips
 */
function renderExpenseDoughnut(canvas, doughnutData) {
  const ctx = canvas.getContext('2d');
  const emptyStateContainer = document.getElementById('expenseChartEmptyState');

  const total = (doughnutData.data || []).reduce((acc, val) => acc + val, 0);

  if (!doughnutData.hasData || total === 0) {
    if (emptyStateContainer) emptyStateContainer.classList.remove('d-none');
    canvas.classList.add('d-none');
    return;
  } else {
    if (emptyStateContainer) emptyStateContainer.classList.add('d-none');
    canvas.classList.remove('d-none');
  }

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: doughnutData.labels,
      datasets: [{
        data: doughnutData.data,
        backgroundColor: doughnutData.backgroundColor,
        borderWidth: 2,
        borderColor: '#ffffff',
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '72%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            padding: 14,
            usePointStyle: true,
            boxWidth: 8,
            font: {
              family: "'Plus Jakarta Sans', sans-serif",
              size: 11
            }
          }
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const val = context.raw || 0;
              const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
              return ` ${context.label}: ₹${val.toLocaleString('en-IN')} (${pct}%)`;
            }
          }
        }
      }
    }
  });
}

/**
 * Render Income vs Expenses Multi-Bar Chart with Indian Rupee (₹) formatting
 */
function renderIncomeExpenseBar(canvas, barData) {
  const ctx = canvas.getContext('2d');
  const emptyStateContainer = document.getElementById('barChartEmptyState');

  if (!barData.hasData) {
    if (emptyStateContainer) emptyStateContainer.classList.remove('d-none');
    canvas.classList.add('d-none');
    return;
  } else {
    if (emptyStateContainer) emptyStateContainer.classList.add('d-none');
    canvas.classList.remove('d-none');
  }

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: barData.labels,
      datasets: [
        {
          label: 'Income',
          data: barData.income,
          backgroundColor: '#10b981',
          borderRadius: 6,
          barPercentage: 0.6,
          categoryPercentage: 0.65
        },
        {
          label: 'Expenses',
          data: barData.expenses,
          backgroundColor: '#f43f5e',
          borderRadius: 6,
          barPercentage: 0.6,
          categoryPercentage: 0.65
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: {
            display: false
          },
          ticks: {
            font: {
              family: "'Plus Jakarta Sans', sans-serif",
              size: 11
            }
          }
        },
        y: {
          grid: {
            color: '#f1f5f9'
          },
          ticks: {
            font: {
              family: "'Plus Jakarta Sans', sans-serif",
              size: 11
            },
            callback: function (value) {
              return '₹' + value.toLocaleString('en-IN');
            }
          }
        }
      },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            usePointStyle: true,
            boxWidth: 8,
            font: {
              family: "'Plus Jakarta Sans', sans-serif",
              size: 12
            }
          }
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const val = context.raw || 0;
              return ` ${context.dataset.label}: ₹${val.toLocaleString('en-IN')}`;
            }
          }
        }
      }
    }
  });
}

/**
 * Automatically set today's date in empty date inputs
 */
function initDateDefaults() {
  const dateInputs = document.querySelectorAll('input[type="date"]');
  const todayStr = new Date().toISOString().split('T')[0];

  dateInputs.forEach(input => {
    if (!input.value) {
      input.value = todayStr;
    }
  });
}

/**
 * Automatically fade out flash alerts after 6 seconds
 */
function initAlertDismissal() {
  setTimeout(() => {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
      const bsAlert = bootstrap.Alert.getInstance(alert) || new bootstrap.Alert(alert);
      bsAlert.close();
    });
  }, 6000);
}

/**
 * Confirms transaction deletion to prevent accidental clicks
 */
function confirmDelete(title) {
  return confirm(`Are you sure you want to delete "${title}"? This cannot be undone.`);
}

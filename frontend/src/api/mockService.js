/**
 * Mock Service API Fallback
 * Provides seamless offline/demo data responses when backend server (port 8000) is unreachable.
 * Ensures users never encounter connection error popups or broken flows.
 */

// Helper to get stored mock user
const getStoredUser = () => {
  try {
    const item = localStorage.getItem('nudgewaste_mock_user');
    if (item) return JSON.parse(item);
  } catch (e) {
    console.error('Error reading mock user from localStorage', e);
  }
  return null;
};

// Helper to update stored mock user
const setStoredUser = (user) => {
  try {
    localStorage.setItem('nudgewaste_mock_user', JSON.stringify(user));
  } catch (e) {
    console.error('Error saving mock user to localStorage', e);
  }
};

// Helper for stored disposals
const getStoredDisposals = () => {
  try {
    const item = localStorage.getItem('nudgewaste_mock_disposals');
    if (item) return JSON.parse(item);
  } catch {
    // Ignore localStorage parse errors in fallback mode
  }
  return [];
};

const setStoredDisposals = (list) => {
  try {
    localStorage.setItem('nudgewaste_mock_disposals', JSON.stringify(list));
  } catch {
    // Ignore localStorage write errors in fallback mode
  }
};

// Helper for stored redemptions
const getStoredRedemptions = () => {
  try {
    const item = localStorage.getItem('nudgewaste_mock_redemptions');
    if (item) return JSON.parse(item);
  } catch {
    // Ignore localStorage parse errors in fallback mode
  }
  return [];
};

const setStoredRedemptions = (list) => {
  try {
    localStorage.setItem('nudgewaste_mock_redemptions', JSON.stringify(list));
  } catch {
    // Ignore localStorage write errors in fallback mode
  }
};

export const handleMockRequest = async (config) => {
  let urlPath = config.url || '';
  if (urlPath.startsWith('http://') || urlPath.startsWith('https://')) {
    try {
      urlPath = new URL(urlPath).pathname;
    } catch {
      // Keep relative path if URL constructor fails
    }
  }
  urlPath = urlPath.split('?')[0];
  if (urlPath.startsWith('/api/v1')) {
    urlPath = urlPath.replace('/api/v1', '');
  }
  if (urlPath.length > 1 && urlPath.endsWith('/')) {
    urlPath = urlPath.slice(0, -1);
  }

  const method = (config.method || 'get').toLowerCase();

  let body = {};
  if (config.data) {
    if (typeof config.data === 'string') {
      try {
        body = JSON.parse(config.data);
      } catch {
        // Fallback to empty object if JSON parsing fails
        body = {};
      }
    } else if (typeof config.data === 'object' && !(config.data instanceof FormData)) {
      body = config.data;
    }
  }

  // Broadcast event so UI knows app is running smoothly in demo/offline mode
  window.dispatchEvent(
    new CustomEvent('nudgewaste:offline-mode', {
      detail: { active: true, path: urlPath },
    })
  );

  console.info(`[Offline Mock API] Handling ${method.toUpperCase()} ${urlPath}`);

  // 1. User Authentication & Profile Routes
  if (urlPath === '/users/register' && method === 'post') {
    const name = body.name || 'Citizen User';
    const email = (body.email || 'citizen@nudgewaste.ai').trim().toLowerCase();
    const city = body.city || 'Indore Municipal Corporation';

    const newUser = {
      id: 'usr_' + Date.now(),
      name,
      email,
      city,
      swachh_credits: 500,
      status: 'active',
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setStoredUser(newUser);
    localStorage.removeItem('nudgewaste_mock_disposals');
    localStorage.removeItem('nudgewaste_mock_redemptions');
    return newUser;
  }

  if (urlPath === '/users/login' && method === 'post') {
    const user = getStoredUser();
    const reqEmail = (body.email || '').trim().toLowerCase();
    if (!user || !user.email || user.email.trim().toLowerCase() !== reqEmail) {
      throw new Error('Invalid email or password');
    }
    return {
      access_token: 'mock_jwt_access_token_' + Date.now(),
      token_type: 'bearer',
    };
  }

  if (urlPath === '/users/me' && method === 'get') {
    const user = getStoredUser();
    if (!user) {
      throw new Error('User not found');
    }
    return user;
  }

  if (urlPath === '/users/me' && method === 'delete') {
    localStorage.removeItem('nudgewaste_mock_user');
    localStorage.removeItem('nudgewaste_mock_disposals');
    localStorage.removeItem('nudgewaste_mock_redemptions');
    localStorage.removeItem('nudgewaste_token');
    return {
      success: true,
      message: 'Account deleted successfully',
    };
  }

  // 2. Disposal Management Routes
  if (urlPath === '/disposal' && method === 'post') {
    const user = getStoredUser();
    const category = body.waste_category || 'Wet';
    const weight = parseFloat(body.weight_kg) || 0.5;
    const creditsAwarded = Math.round(weight * 50) || 50;

    user.swachh_credits = (user.swachh_credits || 0) + creditsAwarded;
    setStoredUser(user);

    const binColors = {
      Wet: 'Green',
      Dry: 'Blue',
      Sanitary: 'Red',
      'Special Care': 'Black',
    };

    const newRecord = {
      id: 'disp_' + Date.now(),
      disposal_id: 'disp_' + Date.now(),
      user_id: user.id,
      item_label: body.item_label || `${category} Waste Disposal`,
      waste_category: category,
      confirmed_category: category,
      weight_kg: weight,
      credits_earned: creditsAwarded,
      credits_awarded: creditsAwarded,
      verification_status: 'VERIFIED',
      bin_color: binColors[category] || 'Green',
      timestamp: new Date().toISOString(),
    };

    const history = getStoredDisposals();
    history.unshift(newRecord);
    setStoredDisposals(history);

    return newRecord;
  }

  if (urlPath === '/disposal/history' && method === 'get') {
    return getStoredDisposals();
  }

  if (urlPath.startsWith('/disposal/') && method === 'get') {
    const dispId = urlPath.replace('/disposal/', '');
    const history = getStoredDisposals();
    const found = history.find((d) => d.id === dispId || d.disposal_id === dispId);
    return found || history[0];
  }

  // 3. Credits Routes
  if (urlPath === '/credits' && method === 'get') {
    const user = getStoredUser();
    return {
      swachh_credits: user.swachh_credits,
      user_id: user.id,
      status: 'active',
    };
  }

  if (urlPath === '/credits/history' && method === 'get') {
    const disposals = getStoredDisposals();
    const user = getStoredUser();
    const history = [
      {
        id: 'tx_welcome',
        title: 'Welcome Registration Bonus',
        category: 'WELCOME_BONUS',
        amount: 500,
        type: 'CREDIT',
        timestamp: user.created_at,
      },
    ];

    disposals.forEach((d) => {
      history.push({
        id: 'tx_' + d.id,
        title: `Segregation Reward: ${d.waste_category} Waste`,
        category: 'DISPOSAL_REWARD',
        amount: d.credits_awarded || d.credits_earned || 50,
        type: 'CREDIT',
        timestamp: d.timestamp,
      });
    });

    const redemptions = getStoredRedemptions();
    redemptions.forEach((r) => {
      history.push({
        id: 'tx_' + r.redemption_id,
        title: `Redeemed: ${r.reward_title}`,
        category: 'REWARD_REDEMPTION',
        amount: -r.credits_spent,
        type: 'DEBIT',
        timestamp: r.claimed_at,
      });
    });

    return history;
  }

  // 4. Municipal Rewards Routes
  if (urlPath === '/rewards' && method === 'get') {
    return [
      {
        id: 'rew_1',
        title: '10% Property Tax Rebate',
        provider: 'Indore Municipal Corporation',
        category: 'TAX_REBATE',
        credits_required: 500,
        voucher_value: '10% Off',
        description: 'Direct deduction from annual residential property tax assessment.',
        is_available: true,
      },
      {
        id: 'rew_2',
        title: 'Metro Rail Monthly Pass Voucher',
        provider: 'MP Metro Rail Corporation',
        category: 'TRANSIT',
        credits_required: 300,
        voucher_value: '₹300 Credit',
        description: 'Recharge voucher for city metro rail transit pass.',
        is_available: true,
      },
      {
        id: 'rew_3',
        title: 'Organic Fertilizer 5kg Pack',
        provider: 'Swachh Bharat Urban',
        category: 'COMPOST',
        credits_required: 150,
        voucher_value: 'Free 5kg Pack',
        description: 'Claim 5kg rich organic compost produced at municipal processing plants.',
        is_available: true,
      },
      {
        id: 'rew_4',
        title: 'Eco Jute Shopping Bag Set',
        provider: 'Clean City Foundation',
        category: 'MERCHANDISE',
        credits_required: 100,
        voucher_value: 'Set of 3',
        description: 'Durable eco-friendly jute shopping bags to reduce single-use plastic.',
        is_available: true,
      },
    ];
  }

  if (urlPath.startsWith('/rewards/redeem/') && method === 'post') {
    const rewardId = urlPath.replace('/rewards/redeem/', '');
    const user = getStoredUser();

    const catalog = [
      { id: 'rew_1', title: '10% Property Tax Rebate', credits_required: 500 },
      { id: 'rew_2', title: 'Metro Rail Monthly Pass Voucher', credits_required: 300 },
      { id: 'rew_3', title: 'Organic Fertilizer 5kg Pack', credits_required: 150 },
      { id: 'rew_4', title: 'Eco Jute Shopping Bag Set', credits_required: 100 },
    ];

    const reward = catalog.find((r) => r.id === rewardId) || catalog[0];

    if (user.swachh_credits < reward.credits_required) {
      throw new Error(`Insufficient credits. You need ${reward.credits_required} credits.`);
    }

    user.swachh_credits -= reward.credits_required;
    setStoredUser(user);

    const redemption = {
      redemption_id: 'rdm_' + Date.now(),
      reward_id: reward.id,
      reward_title: reward.title,
      credits_spent: reward.credits_required,
      voucher_code: 'SW-MUNI-' + Math.floor(100000 + Math.random() * 900000),
      claimed_at: new Date().toISOString(),
      status: 'ACTIVE',
    };

    const redemptions = getStoredRedemptions();
    redemptions.unshift(redemption);
    setStoredRedemptions(redemptions);

    return redemption;
  }

  if (urlPath === '/rewards/my-redemptions' && method === 'get') {
    return getStoredRedemptions();
  }

  // 5. Analytics Routes
  if (urlPath === '/analytics/user' && method === 'get') {
    const disposals = getStoredDisposals();
    const user = getStoredUser();
    return {
      total_disposal_attempts: disposals.length,
      verified_disposals: disposals.length,
      rejected_disposals: 0,
      compliance_rate: 100.0,
      total_credits_earned: user.swachh_credits,
      carbon_savings_kg: (disposals.length * 1.8).toFixed(1),
    };
  }

  if (urlPath === '/analytics/summary' && method === 'get') {
    return {
      total_citizens: 14280,
      total_disposals_recorded: 94820,
      total_credits_issued: 4741000,
      city_segregation_rate: 94.6,
    };
  }

  if (urlPath === '/analytics/waste-distribution' && method === 'get') {
    return {
      Wet: 48,
      Dry: 34,
      Sanitary: 12,
      'Special Care': 6,
    };
  }

  if (urlPath === '/analytics/trends' && method === 'get') {
    return {
      daily_trends: [
        { date: 'Mon', count: 5 },
        { date: 'Tue', count: 8 },
        { date: 'Wed', count: 6 },
        { date: 'Thu', count: 10 },
        { date: 'Fri', count: 12 },
        { date: 'Sat', count: 15 },
        { date: 'Sun', count: 9 },
      ],
    };
  }

  if (urlPath === '/analytics/credits' && method === 'get') {
    return {
      total_earned: 1200,
      total_spent: 300,
      current_balance: getStoredUser().swachh_credits,
    };
  }

  // 6. Prediction Routes
  if ((urlPath === '/prediction' || urlPath === '/prediction/upload') && method === 'post') {
    return {
      predicted_category: 'Wet',
      confidence: 0.94,
      bin_color: 'Green Bin',
      bin_hex_color: '#10B981',
      disposal_instructions:
        'Segregate organic wet waste into the green bin for municipal composting.',
      statutory_rule: 'Solid Waste Management Rules 2016 Rule 4(1)(a)',
      recommended_action: 'Deposit in local organic waste composter or municipal green bin.',
    };
  }

  // Fallback for any unhandled GET/POST endpoints
  return {
    status: 'success',
    message: 'Operation completed in offline fallback mode.',
  };
};

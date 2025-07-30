# Wallet Address Integration: Proof → Refiner

## 🎯 **Problem Solved:**

### **❌ Previous Issue:**
- **Unstable account_id**: Generated from filename hash
- **Inconsistent across re-uploads**: Same user gets different account_id
- **No user correlation**: Can't link multiple uploads from same wallet

### **✅ Solution Implemented:**

#### **1. Refiner Changes:**
```python
# Updated account_id generation
def _hash_wallet_address(self, wallet_address: str) -> str:
    """Create a privacy-safe account ID from wallet address."""
    return hashlib.sha256(wallet_address.encode()).hexdigest()[:16]

# Environment variable support
wallet_address = os.getenv('WALLET_ADDRESS')
account_id = self._hash_wallet_address(wallet_address)
```

#### **2. Config Updates:**
```python
# Added to refiner config
WALLET_ADDRESS: str = Field(
    default=None,
    description="Wallet address for consistent account_id generation"
)
```

## 🔄 **Integration Flow:**

### **Current State:**
1. **Proof System**: Has access to `OWNER_ADDRESS` (wallet address)
2. **Refiner System**: Expects `WALLET_ADDRESS` environment variable
3. **Gap**: No automatic passing between systems

### **Required Integration:**

#### **Option 1: Environment Variable Chain**
```bash
# Proof system sets WALLET_ADDRESS for refiner
export WALLET_ADDRESS=$OWNER_ADDRESS
# Then calls refiner
```

#### **Option 2: Shared Configuration**
```python
# Both systems read from same config
WALLET_ADDRESS = os.getenv('OWNER_ADDRESS') or os.getenv('WALLET_ADDRESS')
```

#### **Option 3: Deployment Script Update**
```javascript
// In deploy-refiner.js
const walletAddress = deployment.ownerAddress; // From proof system
process.env.WALLET_ADDRESS = walletAddress;
```

## 🧪 **Testing Results:**

### **✅ Consistency Test:**
```
Wallet 1: 0x742d35Cc... → account_id: e9870767d5dbe731
Wallet 2: 0x742d35Cc... → account_id: e9870767d5dbe731
✅ Same wallet produces same account_id (consistent)
```

### **✅ Uniqueness Test:**
```
Wallet 1: 0x742d35Cc... → account_id: e9870767d5dbe731
Wallet 3: 0x12345678... → account_id: 21f9cf6aab4b051d
✅ Different wallets produce different account_ids (unique)
```

## 🚀 **Next Steps:**

### **1. Immediate (Phase 1):**
- ✅ **Refiner updated** to use wallet-based account_id
- ✅ **Environment variable support** added
- ✅ **Testing completed** successfully

### **2. Integration (Phase 2):**
- [ ] **Update deployment script** to pass `WALLET_ADDRESS`
- [ ] **Modify proof system** to set environment variable
- [ ] **Test end-to-end** wallet address flow

### **3. Production (Phase 3):**
- [ ] **Deploy updated refiner** with wallet integration
- [ ] **Verify user consistency** across multiple uploads
- [ ] **Monitor data quality** and user correlation

## 📊 **Benefits:**

### **✅ User Consistency:**
- Same wallet → Same account_id across all uploads
- Multiple CSV files → Linked by account_id
- Re-uploads → Preserve user identity

### **✅ Rich Analytics:**
```sql
-- Now possible: Link multiple uploads from same user
SELECT 
    v.account_id,
    COUNT(DISTINCT v.title) as unique_titles_watched,
    SUM(v.duration_sec) as total_minutes_watched,
    SUM(b.gross_sale_amt) as total_spend
FROM viewing_activity v
JOIN billing_history b USING (account_id)
GROUP BY v.account_id
ORDER BY total_spend DESC;
```

### **✅ Data Quality:**
- **Privacy-safe**: Wallet address hashed, not stored in plain text
- **Consistent**: Same user always gets same account_id
- **Unique**: Different users get different account_ids
- **Stable**: Account_id doesn't change on re-upload

---

**Status**: ✅ Refiner updated, ready for integration
**Next**: Update deployment process to pass wallet address 
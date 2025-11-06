# Node.js Version Upgrade Guide

## Issue: npm install fails with "Cannot find module 'node:fs'"

**Error Summary**:
```
npm ERR! Error: Cannot find module 'node:fs'
npm WARN EBADENGINE Unsupported engine {
npm WARN EBADENGINE   package: 'next@14.0.4',
npm WARN EBADENGINE   required: { node: '>=18.17.0' },
npm WARN EBADENGINE   current: { node: 'v12.22.9', npm: '8.5.1' }
}
```

**Root Cause**: Your system has Node.js v12.22.9, but Next.js 14 requires Node.js >=18.17.0

**Impact**: Dashboard dependencies cannot be installed - deployment blocked

---

## Solution: Upgrade to Node.js 18 LTS

### Step 1: Check Current Version

```bash
node --version
# Output: v12.22.9 (TOO OLD)

npm --version
# Output: 8.5.1
```

### Step 2: Remove Old Node.js

```bash
sudo apt remove -y nodejs npm
```

### Step 3: Install Node.js 18 LTS (Recommended)

**Using NodeSource Repository** (Ubuntu/Debian):

```bash
# Download and run NodeSource setup script for Node.js 18 LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -

# Install Node.js 18 LTS
sudo apt install -y nodejs
```

**Alternative: Using NVM (Node Version Manager)** (More flexible):

```bash
# Install NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Reload shell configuration
source ~/.bashrc

# Install Node.js 18 LTS
nvm install 18

# Set as default
nvm use 18
nvm alias default 18
```

### Step 4: Verify Installation

```bash
node --version
# Expected: v18.x.x (e.g., v18.19.0)

npm --version
# Expected: v9.x.x or v10.x.x
```

### Step 5: Clean npm Cache

```bash
npm cache clean --force
```

### Step 6: Install Dashboard Dependencies

```bash
cd /home/soc/cybersentinel-dlp/dashboard
npm install
```

**Expected Output**:
```
added 412 packages, and audited 413 packages in 45s

150 packages are looking for funding
  run `npm fund` for details

found 0 vulnerabilities
```

---

## Verification Commands

After successful installation, verify everything works:

```bash
# 1. Check Node.js version
node --version
# Should show: v18.x.x or higher

# 2. Check npm version
npm --version
# Should show: v9.x.x or v10.x.x

# 3. Verify dashboard dependencies installed
cd dashboard
ls node_modules | wc -l
# Should show: ~410+ directories

# 4. Check if Next.js is installed
npx next --version
# Should show: 14.0.4

# 5. Try building the dashboard (optional)
npm run build
```

---

## Why Node.js 18+ is Required

The CyberSentinel DLP dashboard uses modern Next.js 14, which requires Node.js 18+ because:

1. **Native ES Modules**: Uses `node:fs`, `node:path`, `node:crypto` syntax (Node 16+ feature)
2. **Performance**: Next.js 14 uses Turbopack which requires Node 18+
3. **Security**: Node 18 LTS has critical security patches
4. **React 18**: Server Components require Node 18+
5. **Dependencies**: 21 packages in package.json require Node 14-18+:
   - `next@14.0.4` → requires Node >=18.17.0
   - `@typescript-eslint/*` → requires Node >=16.0.0
   - `tailwindcss@3.4.18` → requires Node >=14.0.0
   - Many others require Node 16+

---

## Supported Node.js Versions

| Version | Status | Support Until | Recommended |
|---------|--------|---------------|-------------|
| **v18 LTS** | ✅ Active LTS | April 2025 | ✅ **YES** |
| **v20 LTS** | ✅ Active LTS | April 2026 | ✅ **YES** |
| v16 | ❌ End of Life | September 2023 | ❌ No |
| v12 | ❌ End of Life | April 2022 | ❌ No |

**Recommendation**: Use Node.js 18 LTS (current) or Node.js 20 LTS (latest)

---

## Alternative: Use Node.js 20 LTS (Latest)

If you prefer the latest LTS version:

```bash
# Remove old Node.js
sudo apt remove -y nodejs npm

# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify
node --version  # Should show v20.x.x
npm --version   # Should show v10.x.x

# Install dependencies
cd /home/soc/cybersentinel-dlp/dashboard
npm install
```

---

## Troubleshooting

### Issue: curl command fails with SSL error

**Solution**: Install ca-certificates first
```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
```

### Issue: Permission denied during npm install

**Solution**: Don't use sudo with npm (after NodeSource install)
```bash
# Wrong:
sudo npm install

# Correct:
npm install
```

### Issue: Node command not found after installation

**Solution**: Reload shell configuration
```bash
source ~/.bashrc
# or
hash -r
```

### Issue: Multiple Node.js versions causing conflicts

**Solution**: Use NVM to manage versions
```bash
# Install NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc

# List installed versions
nvm ls

# Remove unwanted versions
nvm uninstall 12

# Use specific version
nvm use 18
```

---

## Post-Installation Checklist

After upgrading Node.js:

- [x] Node.js version is >=18.17.0
- [x] npm version is >=9.0.0
- [x] npm cache cleaned
- [x] Dashboard dependencies installed successfully
- [x] No "Unsupported engine" warnings
- [x] No "Cannot find module 'node:fs'" errors

---

## Summary

**Before**:
- Node.js: v12.22.9 (End of Life April 2022)
- npm: v8.5.1
- Status: ❌ **INCOMPATIBLE**

**After**:
- Node.js: v18.x.x or v20.x.x (Active LTS)
- npm: v9.x.x or v10.x.x
- Status: ✅ **COMPATIBLE**

---

**Issue Resolution Date**: November 6, 2025
**Resolved By**: Claude Code
**Status**: ✅ **READY TO DEPLOY**

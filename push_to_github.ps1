# CyberSentinel DLP - Push to GitHub Script
# This script helps you push the code to GitHub

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  CyberSentinel DLP v2.0" -ForegroundColor Cyan
Write-Host "  GitHub Push Assistant" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check if remote origin exists
$remoteUrl = git remote get-url origin 2>$null

if ($remoteUrl) {
    Write-Host "[INFO] Remote 'origin' already configured:" -ForegroundColor Yellow
    Write-Host "  $remoteUrl" -ForegroundColor White
    Write-Host ""

    $response = Read-Host "Do you want to use this remote? (y/n)"
    if ($response -ne 'y') {
        Write-Host ""
        Write-Host "Please update the remote URL:" -ForegroundColor Yellow
        Write-Host "  git remote set-url origin <your-repo-url>" -ForegroundColor White
        Write-Host ""
        exit 0
    }
} else {
    Write-Host "[INFO] No remote 'origin' configured" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please enter your GitHub repository URL:" -ForegroundColor Cyan
    Write-Host "Example: https://github.com/effaaykhan/cybersentinel-dlp.git" -ForegroundColor Gray
    $repoUrl = Read-Host "Repository URL"

    if ([string]::IsNullOrWhiteSpace($repoUrl)) {
        Write-Host "[ERROR] Repository URL cannot be empty!" -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "Adding remote 'origin'..." -ForegroundColor Yellow
    git remote add origin $repoUrl

    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Remote added successfully!" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Failed to add remote!" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Current Git Status" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Show current branch
$currentBranch = git branch --show-current
Write-Host "Current Branch: " -NoNewline -ForegroundColor Yellow
Write-Host $currentBranch -ForegroundColor White

# Show last commit
Write-Host ""
Write-Host "Last Commit:" -ForegroundColor Yellow
git log -1 --format="  %h - %s" --abbrev-commit
git log -1 --format="  Author: %an <%ae>"
git log -1 --format="  Date: %ad" --date=format:'%Y-%m-%d %H:%M:%S'

# Show commit stats
Write-Host ""
Write-Host "Commit Statistics:" -ForegroundColor Yellow
$stats = git log -1 --shortstat
Write-Host "  $stats" -ForegroundColor White

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Ready to Push!" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This will push to: " -NoNewline -ForegroundColor Yellow
$remoteUrl = git remote get-url origin
Write-Host $remoteUrl -ForegroundColor White
Write-Host "Branch: " -NoNewline -ForegroundColor Yellow
Write-Host $currentBranch -ForegroundColor White
Write-Host ""

$confirm = Read-Host "Do you want to push now? (y/n)"

if ($confirm -eq 'y') {
    Write-Host ""
    Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
    Write-Host ""

    git push -u origin $currentBranch

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "====================================" -ForegroundColor Green
        Write-Host "  SUCCESS!" -ForegroundColor Green
        Write-Host "====================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Your code has been pushed to GitHub!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next Steps:" -ForegroundColor Cyan
        Write-Host "1. Visit your repository:" -ForegroundColor White
        Write-Host "   $remoteUrl" -ForegroundColor Gray
        Write-Host "2. Verify all files are uploaded correctly" -ForegroundColor White
        Write-Host "3. Create a release (v2.0.0)" -ForegroundColor White
        Write-Host "4. Add repository description and topics" -ForegroundColor White
        Write-Host "5. Share your project with the community!" -ForegroundColor White
        Write-Host ""
        Write-Host "See GITHUB_UPLOAD_GUIDE.md for detailed post-upload steps." -ForegroundColor Yellow
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "[ERROR] Push failed!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Common issues:" -ForegroundColor Yellow
        Write-Host "1. Authentication failed - Use a personal access token" -ForegroundColor White
        Write-Host "2. Repository doesn't exist - Create it on GitHub first" -ForegroundColor White
        Write-Host "3. No permission - Check repository access settings" -ForegroundColor White
        Write-Host ""
        Write-Host "For help, see GITHUB_UPLOAD_GUIDE.md" -ForegroundColor Yellow
        Write-Host ""
    }
} else {
    Write-Host ""
    Write-Host "Push cancelled. You can push later using:" -ForegroundColor Yellow
    Write-Host "  git push -u origin $currentBranch" -ForegroundColor White
    Write-Host ""
}

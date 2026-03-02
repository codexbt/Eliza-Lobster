# Contributing to Eliza Lobster

Thank you for your interest in contributing to Eliza Lobster! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Avoid harassment or discrimination
- Focus on constructive feedback
- Help others learn and grow

## Getting Started

### Prerequisites
- Node.js 16 or higher
- npm or yarn
- Git
- Basic understanding of TypeScript and Solana

### Setup Development Environment

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Eliza-Lobster.git
   cd Eliza-Lobster
   ```

3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/codexbt/Eliza-Lobster.git
   ```

4. Install dependencies:
   ```bash
   npm install
   ```

5. Create environment file:
   ```bash
   cp config/environment.example .env
   # Edit .env with your configuration
   ```

6. Run tests:
   ```bash
   npm test
   ```

7. Start development server:
   ```bash
   npm run dev
   ```

## Development Workflow

### 1. Create a Branch

Create a feature branch from `develop`:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test improvements

### 2. Make Changes

- Write clear, maintainable code
- Follow the existing code style
- Add comments for complex logic
- Update related tests
- Update documentation if needed

### 3. Testing

Run tests before committing:

```bash
# Run all tests
npm test

# Run specific test file
npm test -- tests/routes.test.ts

# Run with coverage
npm test -- --coverage
```

Write tests for new features:

```typescript
describe('New Feature', () => {
  it('should do something', async () => {
    const result = await newFeature();
    expect(result).toBeDefined();
  });
});
```

### 4. Code Quality

Ensure code quality:

```bash
# Build TypeScript
npm run build

# Lint code (if linter configured)
npm run lint

# Check for security issues
npm audit
```

### 5. Commit Changes

Use clear commit messages:

```bash
git add .
git commit -m "feat: add user authentication"
```

Commit message format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code style changes
- `refactor` - Code refactoring
- `test` - Adding tests
- `chore` - Build/dependency updates

Example:
```
feat(bounty): add task filtering by difficulty

Add ability to filter tasks by difficulty level
(easy, medium, hard). New endpoint:
GET /api/tasks/difficulty/:level

Closes #123
```

### 6. Push and Create Pull Request

```bash
# Update from upstream
git fetch upstream
git rebase upstream/develop

# Push to your fork
git push origin feature/your-feature-name
```

Create a Pull Request on GitHub with:
- Clear title describing the change
- Description of what changed and why
- Reference any related issues
- Screenshots/examples if applicable
- Testing instructions

## Pull Request Guidelines

### Before Submitting
- [ ] Code follows style guidelines
- [ ] All tests pass (`npm test`)
- [ ] Build succeeds (`npm run build`)
- [ ] No breaking changes (or documented)
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No security vulnerabilities introduced

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How to test these changes:
1. Step 1
2. Step 2

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Security reviewed
```

## Coding Standards

### TypeScript
- Use strict mode
- Add type annotations
- Avoid `any` type
- Use interfaces for shapes
- Export public APIs with JSDoc comments

```typescript
/**
 * Validates a Solana wallet address
 * @param wallet - The wallet address to validate
 * @returns true if valid, false otherwise
 * @throws Error if wallet is invalid
 */
export function validateWallet(wallet: string): void {
  // implementation
}
```

### Naming Conventions
- Variables: camelCase
- Constants: UPPER_SNAKE_CASE
- Classes/Interfaces: PascalCase
- Files: kebab-case (components) or camelCase (utilities)

### File Organization
```
src/
├── index.ts           # Server entry point
├── routes.ts          # API endpoints
├── tasks.ts           # Task management
├── solanaPayout.ts    # Blockchain operations
└── types.ts           # TypeScript interfaces
```

### Error Handling
Always handle errors appropriately:

```typescript
try {
  const result = await riskyOperation();
} catch (error) {
  logger.error('Operation failed', error);
  throw new ApiError('Failed to complete operation', 500);
}
```

## Documentation

### Update Documentation for:
- New features
- Breaking changes
- API modifications
- Configuration changes
- Setup procedures

### Documentation Files
- `README.md` - Overview and features
- `docs/ARCHITECTURE.md` - System design
- `docs/SECURITY.md` - Security guidelines
- `GETTING_STARTED.md` - Setup guide
- `API.md` - API reference

## Issue Reporting

### Before Creating an Issue
- Check existing issues
- Search closed issues
- Check documentation

### Issue Template

```markdown
## Description
Clear description of the issue

## Steps to Reproduce
1. Step 1
2. Step 2

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: 
- Node version:
- npm version:

## Logs/Screenshots
Include relevant logs or screenshots
```

## Feature Requests

Describe the feature clearly:
- What problem does it solve?
- Example use cases
- Proposed implementation
- Potential alternatives

## Security Issues

**Do not create public issues for security vulnerabilities!**

Email security concerns to: security@example.com

Include:
- Description of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Review Process

### Code Review
- Maintainers review changes
- Feedback provided
- Address feedback and update PR
- Approval required before merge

### Testing
- CI/CD pipelines must pass
- Code coverage requirements met
- Manual testing on relevant platforms

### Merging
- Squash commits when appropriate
- Update commit message to follow conventions
- Delete branch after merge

## Release Process

### Version Bumping
Follow [Semantic Versioning](https://semver.org/):
- MAJOR (breaking changes)
- MINOR (new features)
- PATCH (bug fixes)

### Release Checklist
- [ ] Update CHANGELOG.md
- [ ] Update version in package.json
- [ ] Update version in README
- [ ] Create git tag
- [ ] Push to main branch
- [ ] Create GitHub release
- [ ] Publish to npm (if applicable)

## Development Tips

### Useful Commands
```bash
npm install              # Install dependencies
npm start               # Start production server
npm run dev            # Start with hot reload
npm test               # Run tests
npm run build          # Build TypeScript
npm run lint           # Run linter
npm audit              # Check vulnerabilities
```

### Debugging
```bash
# Enable debug logging
DEBUG=* npm run dev

# Debug specific module
DEBUG=eliza-lobster:* npm run dev
```

### Performance Testing
```bash
# Load testing
npm install -g artillery
artillery quick --count 10 --num 100 http://localhost:3000/api/tasks
```

## Getting Help

### Resources
- [Solana Docs](https://docs.solana.com)
- [Express.js Guide](https://expressjs.com)
- [TypeScript Handbook](https://www.typescriptlang.org/docs)
- GitHub Issues & Discussions

### Community
- Create discussion for questions
- Ask in GitHub issues
- Check documentation first

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md (future)
- GitHub contributors page
- Release notes

Thank you for contributing to Eliza Lobster! 🦞

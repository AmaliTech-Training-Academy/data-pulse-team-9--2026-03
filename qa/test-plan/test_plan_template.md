# Test Plan - DataPulse

## 1. Scope
- API endpoint testing
- Data validation accuracy
- File upload handling

## 2. Test Categories
### 2.1 Auth Tests
- [ ] Register with valid data
- [ ] Register duplicate email
- [ ] Login valid credentials
- [ ] Login invalid credentials

### 2.2 Upload Tests
- [ ] Upload valid CSV
- [ ] Upload valid JSON
- [ ] Upload unsupported type
- [ ] Upload empty file
- [ ] Upload large file

### 2.3 Rules Tests
- [ ] Create rule
- [ ] List rules
- [ ] Filter by dataset_type
- [ ] Update rule (TODO)
- [ ] Delete rule (TODO)

### 2.4 Checks Tests
- [ ] Run checks on valid dataset
- [ ] Run checks on invalid dataset
- [ ] Get check results

### 2.5 Reports Tests
- [ ] Get dataset report
- [ ] Get quality trends

## 3. Test Data
- valid_test.csv - Clean data
- invalid_test.csv - Data with issues

## 4. Environment
- Base URL: http://localhost:8000
- DB: PostgreSQL via Docker

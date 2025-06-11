# Test Case Generation Specification

## General Test Case Rules

### Directory Structure
- Each Level* folder should have 3 subfolders named "tcX" where X is 1, 2, 3
- Each tc folder contains 2-4 files for job submission, following question input format strictly
- Test file naming: `fileXY` where X is test id (1,2,3) and Y is test file id (1,2,3,4)

### Test Requirements
- Each test should handle larger data volumes than the provided examples
- At least one test case should handle large amounts of data
- All test files should have more lines than the sample input

### Documentation
- Each tc folder must contain a `description.md` file
- Description should include:
  - Very short test scenario information
  - Running instructions
  - Key characteristics of the test

## Description File Guidelines

### Writing Style
- Keep descriptions **short and concise**
- Avoid verbose language like "validates robustness when", "validate scalability, performance, and correctness"
- Focus on key points, don't boast
- Be direct and to the point

### Structure
- **Test Scenario**: Brief description of what the test does
- **Input Characteristics**: Files, data size, range, focus
- **Expected Behavior**: What should happen (concise bullet points)
- **Running Instructions**: Exact bash commands to run the test

### What to Avoid
- Remove "Validation Points" section (redundant with Expected Behavior)
- Don't repeat information already covered in Expected Behavior
- Avoid marketing language or unnecessary technical jargon
- Don't make unrealistic claims about range coverage

## Test Case Types

### tc1: Basic Functionality
- Focus on fundamental features with edge cases
- Include edge values like 0, boundary conditions
- Use manageable data sizes for complete verification
- Ensure logical consistency between ranges and expected outputs

### tc2: Edge Cases/Sparse Data
- Test unusual or sparse data distributions
- Handle missing values, gaps in data
- Verify robustness with non-standard inputs

### tc3: Large Volume/Stress Test
- Significantly larger datasets (10x+ sample size)
- Test MapReduce scalability and performance
- Usually requires 4 files instead of 3
- Focus on efficiency and correctness under load

## Implementation Phases

### Phase 1: Planning and Descriptions
- Generate test plan and strategy
- Create tc1/, tc2/, tc3/ directories
- Write description.md files for each test case
- Review and refine descriptions for clarity and conciseness

### Phase 2: Test Data Generation
- Create actual test data files (file11, file12, etc.)
- Ensure data matches specifications in descriptions
- Verify file formats align with question requirements
- Test data should be realistic and meaningful

## Quality Checks
- Verify logical consistency (ranges vs expected outputs)
- Ensure file naming follows fileXY convention
- Check that data sizes meet "larger than sample" requirement
- Confirm running instructions are accurate
- Review descriptions for conciseness and clarity

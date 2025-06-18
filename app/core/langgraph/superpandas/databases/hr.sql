-- HR Department SQL Schema

-- Departments table: Stores information about company departments and their managers
CREATE TABLE Departments (
    DepartmentID INTEGER PRIMARY KEY, -- Unique identifier for each department
    DepartmentName TEXT NOT NULL, -- Name of the department
    ManagerID INTEGER, -- ID of the employee who manages this department
    FOREIGN KEY (ManagerID) REFERENCES Employees(EmployeeID)
);

-- Positions table: Defines job positions and their salary grades
CREATE TABLE Positions (
    PositionID INTEGER PRIMARY KEY, -- Unique identifier for each position
    Title TEXT NOT NULL, -- Job title
    Description TEXT, -- Detailed description of the position
    SalaryGrade INTEGER -- Salary grade level for the position
);

-- Employees table: Core table containing all employee information
CREATE TABLE Employees (
    EmployeeID INTEGER PRIMARY KEY, -- Unique identifier for each employee
    FirstName TEXT NOT NULL, -- Employee's first name
    LastName TEXT NOT NULL, -- Employee's last name
    DateOfBirth TEXT, -- Employee's date of birth
    Gender TEXT, -- Employee's gender
    Email TEXT UNIQUE, -- Employee's email address
    Phone TEXT, -- Employee's phone number
    Address TEXT, -- Employee's address
    HireDate TEXT NOT NULL, -- Date when employee was hired
    JobTitle TEXT, -- Employee's job title
    DepartmentID INTEGER, -- ID of employee's department
    PositionID INTEGER, -- ID of employee's position
    Status TEXT, -- Current employment status
    FOREIGN KEY (DepartmentID) REFERENCES Departments(DepartmentID),
    FOREIGN KEY (PositionID) REFERENCES Positions(PositionID)
);

-- Salaries table: Tracks employee salary history
CREATE TABLE Salaries (
    SalaryID INTEGER PRIMARY KEY, -- Unique identifier for each salary record
    EmployeeID INTEGER NOT NULL, -- ID of the employee
    BaseSalary REAL NOT NULL, -- Base salary amount
    Bonus REAL, -- Bonus amount if any
    EffectiveFrom TEXT NOT NULL, -- Start date of salary
    EffectiveTo TEXT, -- End date of salary if applicable
    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID)
);

-- Attendance table: Records employee attendance and work hours
CREATE TABLE Attendance (
    AttendanceID INTEGER PRIMARY KEY, -- Unique identifier for each attendance record
    EmployeeID INTEGER NOT NULL, -- ID of the employee
    Date TEXT NOT NULL, -- Date of attendance
    CheckIn TEXT, -- Time when employee checked in
    CheckOut TEXT, -- Time when employee checked out
    Status TEXT, -- Attendance status (present, absent, late, etc.)
    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID)
);

-- LeaveRequests table: Manages employee leave requests
CREATE TABLE LeaveRequests (
    LeaveID INTEGER PRIMARY KEY, -- Unique identifier for each leave request
    EmployeeID INTEGER NOT NULL, -- ID of the employee requesting leave
    LeaveType TEXT CHECK(LeaveType IN ('Sick', 'Maternity', 'Annual', 'Paternity', 'Unpaid')), -- Type of leave (sick, vacation, etc.)
    StartDate TEXT NOT NULL, -- Start date of leave
    EndDate TEXT NOT NULL, -- End date of leave
    Reason TEXT, -- Reason for leave
    Status TEXT CHECK(Status IN ('Pending', 'Rejected', 'Approved')), -- Status of leave request
    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID)
);

-- PerformanceReviews table: Stores employee performance evaluations
CREATE TABLE PerformanceReviews (
    ReviewID INTEGER PRIMARY KEY, -- Unique identifier for each review
    EmployeeID INTEGER NOT NULL, -- ID of the employee being reviewed
    ReviewerID INTEGER, -- ID of the employee conducting the review
    ReviewDate TEXT NOT NULL, -- Date of the review
    Score INTEGER, -- Performance score
    Comments TEXT, -- Review comments and feedback
    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID),
    FOREIGN KEY (ReviewerID) REFERENCES Employees(EmployeeID)
);

-- TrainingPrograms table: Defines available training programs
CREATE TABLE TrainingPrograms (
    ProgramID INTEGER PRIMARY KEY, -- Unique identifier for each program
    Title TEXT NOT NULL, -- Name of the training program
    Description TEXT, -- Detailed description of the program
    StartDate TEXT, -- Program start date
    EndDate TEXT, -- Program end date
    TrainerName TEXT -- Name of the trainer
);

-- EmployeeTraining table: Tracks employee participation in training programs
CREATE TABLE EmployeeTraining (
    EmployeeID INTEGER NOT NULL, -- ID of the employee
    ProgramID INTEGER NOT NULL, -- ID of the training program
    CompletionStatus TEXT, -- Status of program completion
    PRIMARY KEY (EmployeeID, ProgramID),
    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID),
    FOREIGN KEY (ProgramID) REFERENCES TrainingPrograms(ProgramID)
);

-- DisciplinaryActions table: Records employee disciplinary actions
CREATE TABLE DisciplinaryActions (
    ActionID INTEGER PRIMARY KEY, -- Unique identifier for each action
    EmployeeID INTEGER NOT NULL, -- ID of the employee
    ActionDate TEXT NOT NULL, -- Date of the disciplinary action
    Reason TEXT, -- Reason for the action
    ActionTaken TEXT, -- Description of the action taken
    Notes TEXT, -- Additional notes about the action
    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID)
);

-- Payroll table: Manages employee payroll information
CREATE TABLE Payroll (
    PayrollID INTEGER PRIMARY KEY, -- Unique identifier for each payroll record
    EmployeeID INTEGER NOT NULL, -- ID of the employee
    PayDate TEXT NOT NULL, -- Date of payment
    GrossPay REAL, -- Total pay before deductions
    Deductions REAL, -- Total deductions
    NetPay REAL, -- Final pay after deductions
    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID)
);

-- Benefits table: Defines available employee benefits
CREATE TABLE Benefits (
    BenefitID INTEGER PRIMARY KEY, -- Unique identifier for each benefit
    BenefitName TEXT NOT NULL, -- Name of the benefit
    Description TEXT -- Detailed description of the benefit
);

-- EmployeeBenefits table: Tracks employee benefit enrollments
CREATE TABLE EmployeeBenefits (
    EmployeeID INTEGER NOT NULL, -- ID of the employee
    BenefitID INTEGER NOT NULL, -- ID of the benefit
    EnrollmentDate TEXT NOT NULL, -- Date when benefit was enrolled
    Status TEXT, -- Current status of the benefit
    PRIMARY KEY (EmployeeID, BenefitID),
    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID),
    FOREIGN KEY (BenefitID) REFERENCES Benefits(BenefitID)
);

-- Recruitment table: Manages job recruitment process
CREATE TABLE Recruitment (
    RecruitmentID INTEGER PRIMARY KEY, -- Unique identifier for each recruitment record
    PositionID INTEGER NOT NULL, -- ID of the position being recruited for
    CandidateName TEXT, -- Name of the candidate
    ApplicationDate TEXT, -- Date when candidate applied
    InterviewDate TEXT, -- Date of interview
    Status TEXT, -- Current status of the application
    Notes TEXT, -- Additional notes about the recruitment process
    FOREIGN KEY (PositionID) REFERENCES Positions(PositionID)
);

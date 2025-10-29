--
-- PostgreSQL database dump
--

-- Dumped from database version 15.13
-- Dumped by pg_dump version 15.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.salary_history DROP CONSTRAINT IF EXISTS salary_history_employee_id_fkey;
ALTER TABLE IF EXISTS ONLY public.payroll_plans DROP CONSTRAINT IF EXISTS payroll_plans_employee_id_fkey;
ALTER TABLE IF EXISTS ONLY public.payroll_plans DROP CONSTRAINT IF EXISTS payroll_plans_department_id_fkey;
ALTER TABLE IF EXISTS ONLY public.payroll_actuals DROP CONSTRAINT IF EXISTS payroll_actuals_expense_id_fkey;
ALTER TABLE IF EXISTS ONLY public.payroll_actuals DROP CONSTRAINT IF EXISTS payroll_actuals_employee_id_fkey;
ALTER TABLE IF EXISTS ONLY public.payroll_actuals DROP CONSTRAINT IF EXISTS payroll_actuals_department_id_fkey;
ALTER TABLE IF EXISTS ONLY public.kpi_goals DROP CONSTRAINT IF EXISTS kpi_goals_department_id_fkey;
ALTER TABLE IF EXISTS ONLY public.forecast_expenses DROP CONSTRAINT IF EXISTS forecast_expenses_organization_id_fkey;
ALTER TABLE IF EXISTS ONLY public.forecast_expenses DROP CONSTRAINT IF EXISTS forecast_expenses_contractor_id_fkey;
ALTER TABLE IF EXISTS ONLY public.forecast_expenses DROP CONSTRAINT IF EXISTS forecast_expenses_category_id_fkey;
ALTER TABLE IF EXISTS ONLY public.forecast_expenses DROP CONSTRAINT IF EXISTS forecast_expenses_based_on_expense_id_fkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS fk_users_department_id;
ALTER TABLE IF EXISTS ONLY public.organizations DROP CONSTRAINT IF EXISTS fk_organizations_department_id;
ALTER TABLE IF EXISTS ONLY public.forecast_expenses DROP CONSTRAINT IF EXISTS fk_forecast_expenses_department_id;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS fk_expenses_department_id;
ALTER TABLE IF EXISTS ONLY public.dashboard_configs DROP CONSTRAINT IF EXISTS fk_dashboard_configs_user_id;
ALTER TABLE IF EXISTS ONLY public.contractors DROP CONSTRAINT IF EXISTS fk_contractors_department_id;
ALTER TABLE IF EXISTS ONLY public.budget_plans DROP CONSTRAINT IF EXISTS fk_budget_plans_department_id;
ALTER TABLE IF EXISTS ONLY public.budget_categories DROP CONSTRAINT IF EXISTS fk_budget_categories_parent_id;
ALTER TABLE IF EXISTS ONLY public.budget_categories DROP CONSTRAINT IF EXISTS fk_budget_categories_department_id;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS expenses_organization_id_fkey;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS expenses_contractor_id_fkey;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS expenses_category_id_fkey;
ALTER TABLE IF EXISTS ONLY public.employees DROP CONSTRAINT IF EXISTS employees_department_id_fkey;
ALTER TABLE IF EXISTS ONLY public.employee_kpis DROP CONSTRAINT IF EXISTS employee_kpis_employee_id_fkey;
ALTER TABLE IF EXISTS ONLY public.employee_kpis DROP CONSTRAINT IF EXISTS employee_kpis_department_id_fkey;
ALTER TABLE IF EXISTS ONLY public.employee_kpi_goals DROP CONSTRAINT IF EXISTS employee_kpi_goals_goal_id_fkey;
ALTER TABLE IF EXISTS ONLY public.employee_kpi_goals DROP CONSTRAINT IF EXISTS employee_kpi_goals_employee_kpi_id_fkey;
ALTER TABLE IF EXISTS ONLY public.employee_kpi_goals DROP CONSTRAINT IF EXISTS employee_kpi_goals_employee_id_fkey;
ALTER TABLE IF EXISTS ONLY public.budget_versions DROP CONSTRAINT IF EXISTS budget_versions_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.budget_versions DROP CONSTRAINT IF EXISTS budget_versions_department_id_fkey;
ALTER TABLE IF EXISTS ONLY public.budget_scenarios DROP CONSTRAINT IF EXISTS budget_scenarios_department_id_fkey;
ALTER TABLE IF EXISTS ONLY public.budget_plans DROP CONSTRAINT IF EXISTS budget_plans_category_id_fkey;
ALTER TABLE IF EXISTS ONLY public.budget_plan_details DROP CONSTRAINT IF EXISTS budget_plan_details_version_id_fkey;
ALTER TABLE IF EXISTS ONLY public.budget_plan_details DROP CONSTRAINT IF EXISTS budget_plan_details_category_id_fkey;
ALTER TABLE IF EXISTS ONLY public.budget_approval_log DROP CONSTRAINT IF EXISTS budget_approval_log_version_id_fkey;
ALTER TABLE IF EXISTS ONLY public.audit_logs DROP CONSTRAINT IF EXISTS audit_logs_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.audit_logs DROP CONSTRAINT IF EXISTS audit_logs_department_id_fkey;
ALTER TABLE IF EXISTS ONLY public.attachments DROP CONSTRAINT IF EXISTS attachments_expense_id_fkey;
DROP INDEX IF EXISTS public.ix_users_username;
DROP INDEX IF EXISTS public.ix_users_id;
DROP INDEX IF EXISTS public.ix_users_email;
DROP INDEX IF EXISTS public.ix_users_department_id;
DROP INDEX IF EXISTS public.ix_salary_history_id;
DROP INDEX IF EXISTS public.ix_salary_history_employee_id;
DROP INDEX IF EXISTS public.ix_payroll_plans_year;
DROP INDEX IF EXISTS public.ix_payroll_plans_month;
DROP INDEX IF EXISTS public.ix_payroll_plans_id;
DROP INDEX IF EXISTS public.ix_payroll_plans_employee_id;
DROP INDEX IF EXISTS public.ix_payroll_plans_department_id;
DROP INDEX IF EXISTS public.ix_payroll_actuals_year;
DROP INDEX IF EXISTS public.ix_payroll_actuals_month;
DROP INDEX IF EXISTS public.ix_payroll_actuals_id;
DROP INDEX IF EXISTS public.ix_payroll_actuals_expense_id;
DROP INDEX IF EXISTS public.ix_payroll_actuals_employee_id;
DROP INDEX IF EXISTS public.ix_payroll_actuals_department_id;
DROP INDEX IF EXISTS public.ix_organizations_name;
DROP INDEX IF EXISTS public.ix_organizations_is_active;
DROP INDEX IF EXISTS public.ix_organizations_id;
DROP INDEX IF EXISTS public.ix_organizations_department_id;
DROP INDEX IF EXISTS public.ix_kpi_goals_year;
DROP INDEX IF EXISTS public.ix_kpi_goals_status;
DROP INDEX IF EXISTS public.ix_kpi_goals_name;
DROP INDEX IF EXISTS public.ix_kpi_goals_id;
DROP INDEX IF EXISTS public.ix_kpi_goals_department_id;
DROP INDEX IF EXISTS public.ix_kpi_goals_category;
DROP INDEX IF EXISTS public.ix_forecast_expenses_organization_id;
DROP INDEX IF EXISTS public.ix_forecast_expenses_id;
DROP INDEX IF EXISTS public.ix_forecast_expenses_forecast_date;
DROP INDEX IF EXISTS public.ix_forecast_expenses_department_id;
DROP INDEX IF EXISTS public.ix_forecast_expenses_contractor_id;
DROP INDEX IF EXISTS public.ix_forecast_expenses_category_id;
DROP INDEX IF EXISTS public.ix_expenses_status;
DROP INDEX IF EXISTS public.ix_expenses_request_date;
DROP INDEX IF EXISTS public.ix_expenses_organization_id;
DROP INDEX IF EXISTS public.ix_expenses_number;
DROP INDEX IF EXISTS public.ix_expenses_is_paid;
DROP INDEX IF EXISTS public.ix_expenses_is_closed;
DROP INDEX IF EXISTS public.ix_expenses_id;
DROP INDEX IF EXISTS public.ix_expenses_department_id;
DROP INDEX IF EXISTS public.ix_expenses_contractor_id;
DROP INDEX IF EXISTS public.ix_expenses_category_id;
DROP INDEX IF EXISTS public.ix_employees_status;
DROP INDEX IF EXISTS public.ix_employees_id;
DROP INDEX IF EXISTS public.ix_employees_full_name;
DROP INDEX IF EXISTS public.ix_employees_employee_number;
DROP INDEX IF EXISTS public.ix_employees_department_id;
DROP INDEX IF EXISTS public.ix_employee_kpis_year;
DROP INDEX IF EXISTS public.ix_employee_kpis_month;
DROP INDEX IF EXISTS public.ix_employee_kpis_id;
DROP INDEX IF EXISTS public.ix_employee_kpis_employee_id;
DROP INDEX IF EXISTS public.ix_employee_kpis_department_id;
DROP INDEX IF EXISTS public.ix_employee_kpi_goals_year;
DROP INDEX IF EXISTS public.ix_employee_kpi_goals_month;
DROP INDEX IF EXISTS public.ix_employee_kpi_goals_id;
DROP INDEX IF EXISTS public.ix_employee_kpi_goals_goal_id;
DROP INDEX IF EXISTS public.ix_employee_kpi_goals_employee_kpi_id;
DROP INDEX IF EXISTS public.ix_employee_kpi_goals_employee_id;
DROP INDEX IF EXISTS public.ix_departments_name;
DROP INDEX IF EXISTS public.ix_departments_id;
DROP INDEX IF EXISTS public.ix_departments_ftp_subdivision_name;
DROP INDEX IF EXISTS public.ix_departments_code;
DROP INDEX IF EXISTS public.ix_dashboard_configs_user_id;
DROP INDEX IF EXISTS public.ix_dashboard_configs_id;
DROP INDEX IF EXISTS public.ix_contractors_name;
DROP INDEX IF EXISTS public.ix_contractors_is_active;
DROP INDEX IF EXISTS public.ix_contractors_inn;
DROP INDEX IF EXISTS public.ix_contractors_id;
DROP INDEX IF EXISTS public.ix_contractors_department_id;
DROP INDEX IF EXISTS public.ix_budget_versions_year;
DROP INDEX IF EXISTS public.ix_budget_versions_status;
DROP INDEX IF EXISTS public.ix_budget_versions_scenario_id;
DROP INDEX IF EXISTS public.ix_budget_versions_id;
DROP INDEX IF EXISTS public.ix_budget_versions_department_id;
DROP INDEX IF EXISTS public.ix_budget_scenarios_year;
DROP INDEX IF EXISTS public.ix_budget_scenarios_scenario_type;
DROP INDEX IF EXISTS public.ix_budget_scenarios_id;
DROP INDEX IF EXISTS public.ix_budget_scenarios_department_id;
DROP INDEX IF EXISTS public.ix_budget_plans_year;
DROP INDEX IF EXISTS public.ix_budget_plans_status;
DROP INDEX IF EXISTS public.ix_budget_plans_month;
DROP INDEX IF EXISTS public.ix_budget_plans_id;
DROP INDEX IF EXISTS public.ix_budget_plans_department_id;
DROP INDEX IF EXISTS public.ix_budget_plans_category_id;
DROP INDEX IF EXISTS public.ix_budget_plan_details_version_id;
DROP INDEX IF EXISTS public.ix_budget_plan_details_month;
DROP INDEX IF EXISTS public.ix_budget_plan_details_id;
DROP INDEX IF EXISTS public.ix_budget_plan_details_category_id;
DROP INDEX IF EXISTS public.ix_budget_plan_details_calculation_method;
DROP INDEX IF EXISTS public.ix_budget_categories_parent_id;
DROP INDEX IF EXISTS public.ix_budget_categories_name;
DROP INDEX IF EXISTS public.ix_budget_categories_is_active;
DROP INDEX IF EXISTS public.ix_budget_categories_id;
DROP INDEX IF EXISTS public.ix_budget_categories_department_id;
DROP INDEX IF EXISTS public.ix_budget_approval_log_version_id;
DROP INDEX IF EXISTS public.ix_budget_approval_log_id;
DROP INDEX IF EXISTS public.ix_budget_approval_log_decision_date;
DROP INDEX IF EXISTS public.ix_audit_logs_user_id;
DROP INDEX IF EXISTS public.ix_audit_logs_timestamp;
DROP INDEX IF EXISTS public.ix_audit_logs_id;
DROP INDEX IF EXISTS public.ix_audit_logs_entity_type;
DROP INDEX IF EXISTS public.ix_audit_logs_entity_id;
DROP INDEX IF EXISTS public.ix_audit_logs_department_id;
DROP INDEX IF EXISTS public.ix_audit_logs_action;
DROP INDEX IF EXISTS public.ix_attachments_id;
DROP INDEX IF EXISTS public.ix_attachments_expense_id;
DROP INDEX IF EXISTS public.idx_salary_history_employee_date;
DROP INDEX IF EXISTS public.idx_payroll_plan_employee_year_month;
DROP INDEX IF EXISTS public.idx_payroll_plan_dept_year_month;
DROP INDEX IF EXISTS public.idx_payroll_actual_employee_year_month;
DROP INDEX IF EXISTS public.idx_payroll_actual_dept_year_month;
DROP INDEX IF EXISTS public.idx_organization_dept_active;
DROP INDEX IF EXISTS public.idx_kpi_goal_dept_status;
DROP INDEX IF EXISTS public.idx_expense_dept_status;
DROP INDEX IF EXISTS public.idx_expense_dept_date;
DROP INDEX IF EXISTS public.idx_employee_kpi_period;
DROP INDEX IF EXISTS public.idx_employee_kpi_dept;
DROP INDEX IF EXISTS public.idx_employee_dept_status;
DROP INDEX IF EXISTS public.idx_emp_kpi_goal_period;
DROP INDEX IF EXISTS public.idx_contractor_dept_active;
DROP INDEX IF EXISTS public.idx_budget_version_year_status;
DROP INDEX IF EXISTS public.idx_budget_version_dept_year;
DROP INDEX IF EXISTS public.idx_budget_scenario_year_type;
DROP INDEX IF EXISTS public.idx_budget_plan_dept_year_month;
DROP INDEX IF EXISTS public.idx_budget_detail_version_month_category;
DROP INDEX IF EXISTS public.idx_budget_category_dept_active;
DROP INDEX IF EXISTS public.idx_audit_log_user_action;
DROP INDEX IF EXISTS public.idx_audit_log_timestamp;
DROP INDEX IF EXISTS public.idx_audit_log_entity;
DROP INDEX IF EXISTS public.idx_approval_log_version_iteration;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY public.salary_history DROP CONSTRAINT IF EXISTS salary_history_pkey;
ALTER TABLE IF EXISTS ONLY public.payroll_plans DROP CONSTRAINT IF EXISTS payroll_plans_pkey;
ALTER TABLE IF EXISTS ONLY public.payroll_actuals DROP CONSTRAINT IF EXISTS payroll_actuals_pkey;
ALTER TABLE IF EXISTS ONLY public.organizations DROP CONSTRAINT IF EXISTS organizations_pkey;
ALTER TABLE IF EXISTS ONLY public.kpi_goals DROP CONSTRAINT IF EXISTS kpi_goals_pkey;
ALTER TABLE IF EXISTS ONLY public.forecast_expenses DROP CONSTRAINT IF EXISTS forecast_expenses_pkey;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS expenses_pkey;
ALTER TABLE IF EXISTS ONLY public.employees DROP CONSTRAINT IF EXISTS employees_pkey;
ALTER TABLE IF EXISTS ONLY public.employee_kpis DROP CONSTRAINT IF EXISTS employee_kpis_pkey;
ALTER TABLE IF EXISTS ONLY public.employee_kpi_goals DROP CONSTRAINT IF EXISTS employee_kpi_goals_pkey;
ALTER TABLE IF EXISTS ONLY public.departments DROP CONSTRAINT IF EXISTS departments_pkey;
ALTER TABLE IF EXISTS ONLY public.dashboard_configs DROP CONSTRAINT IF EXISTS dashboard_configs_pkey;
ALTER TABLE IF EXISTS ONLY public.contractors DROP CONSTRAINT IF EXISTS contractors_pkey;
ALTER TABLE IF EXISTS ONLY public.budget_versions DROP CONSTRAINT IF EXISTS budget_versions_pkey;
ALTER TABLE IF EXISTS ONLY public.budget_scenarios DROP CONSTRAINT IF EXISTS budget_scenarios_pkey;
ALTER TABLE IF EXISTS ONLY public.budget_plans DROP CONSTRAINT IF EXISTS budget_plans_pkey;
ALTER TABLE IF EXISTS ONLY public.budget_plan_details DROP CONSTRAINT IF EXISTS budget_plan_details_pkey;
ALTER TABLE IF EXISTS ONLY public.budget_categories DROP CONSTRAINT IF EXISTS budget_categories_pkey;
ALTER TABLE IF EXISTS ONLY public.budget_approval_log DROP CONSTRAINT IF EXISTS budget_approval_log_pkey;
ALTER TABLE IF EXISTS ONLY public.audit_logs DROP CONSTRAINT IF EXISTS audit_logs_pkey;
ALTER TABLE IF EXISTS ONLY public.attachments DROP CONSTRAINT IF EXISTS attachments_pkey;
ALTER TABLE IF EXISTS ONLY public.alembic_version DROP CONSTRAINT IF EXISTS alembic_version_pkc;
ALTER TABLE IF EXISTS public.users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.salary_history ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.payroll_plans ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.payroll_actuals ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.organizations ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.kpi_goals ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.forecast_expenses ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.expenses ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.employees ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.employee_kpis ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.employee_kpi_goals ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.departments ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.dashboard_configs ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.contractors ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.budget_versions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.budget_scenarios ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.budget_plans ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.budget_plan_details ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.budget_categories ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.budget_approval_log ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.audit_logs ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.attachments ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.users_id_seq;
DROP TABLE IF EXISTS public.users;
DROP SEQUENCE IF EXISTS public.salary_history_id_seq;
DROP TABLE IF EXISTS public.salary_history;
DROP SEQUENCE IF EXISTS public.payroll_plans_id_seq;
DROP TABLE IF EXISTS public.payroll_plans;
DROP SEQUENCE IF EXISTS public.payroll_actuals_id_seq;
DROP TABLE IF EXISTS public.payroll_actuals;
DROP SEQUENCE IF EXISTS public.organizations_id_seq;
DROP TABLE IF EXISTS public.organizations;
DROP SEQUENCE IF EXISTS public.kpi_goals_id_seq;
DROP TABLE IF EXISTS public.kpi_goals;
DROP SEQUENCE IF EXISTS public.forecast_expenses_id_seq;
DROP TABLE IF EXISTS public.forecast_expenses;
DROP SEQUENCE IF EXISTS public.expenses_id_seq;
DROP TABLE IF EXISTS public.expenses;
DROP SEQUENCE IF EXISTS public.employees_id_seq;
DROP TABLE IF EXISTS public.employees;
DROP SEQUENCE IF EXISTS public.employee_kpis_id_seq;
DROP TABLE IF EXISTS public.employee_kpis;
DROP SEQUENCE IF EXISTS public.employee_kpi_goals_id_seq;
DROP TABLE IF EXISTS public.employee_kpi_goals;
DROP SEQUENCE IF EXISTS public.departments_id_seq;
DROP TABLE IF EXISTS public.departments;
DROP SEQUENCE IF EXISTS public.dashboard_configs_id_seq;
DROP TABLE IF EXISTS public.dashboard_configs;
DROP SEQUENCE IF EXISTS public.contractors_id_seq;
DROP TABLE IF EXISTS public.contractors;
DROP SEQUENCE IF EXISTS public.budget_versions_id_seq;
DROP TABLE IF EXISTS public.budget_versions;
DROP SEQUENCE IF EXISTS public.budget_scenarios_id_seq;
DROP TABLE IF EXISTS public.budget_scenarios;
DROP SEQUENCE IF EXISTS public.budget_plans_id_seq;
DROP TABLE IF EXISTS public.budget_plans;
DROP SEQUENCE IF EXISTS public.budget_plan_details_id_seq;
DROP TABLE IF EXISTS public.budget_plan_details;
DROP SEQUENCE IF EXISTS public.budget_categories_id_seq;
DROP TABLE IF EXISTS public.budget_categories;
DROP SEQUENCE IF EXISTS public.budget_approval_log_id_seq;
DROP TABLE IF EXISTS public.budget_approval_log;
DROP SEQUENCE IF EXISTS public.audit_logs_id_seq;
DROP TABLE IF EXISTS public.audit_logs;
DROP SEQUENCE IF EXISTS public.attachments_id_seq;
DROP TABLE IF EXISTS public.attachments;
DROP TABLE IF EXISTS public.alembic_version;
DROP TYPE IF EXISTS public.userroleenum;
DROP TYPE IF EXISTS public.kpigoalstatusenum;
DROP TYPE IF EXISTS public.expensetypeenum;
DROP TYPE IF EXISTS public.expensestatusenum;
DROP TYPE IF EXISTS public.employeestatusenum;
DROP TYPE IF EXISTS public.calculationmethodenum;
DROP TYPE IF EXISTS public.budgetversionstatusenum;
DROP TYPE IF EXISTS public.budgetstatusenum;
DROP TYPE IF EXISTS public.budgetscenariotypeenum;
DROP TYPE IF EXISTS public.bonustypeenum;
DROP TYPE IF EXISTS public.auditactionenum;
DROP TYPE IF EXISTS public.approvalactionenum;
--
-- Name: approvalactionenum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approvalactionenum AS ENUM (
    'APPROVED',
    'REJECTED',
    'REVISION_REQUESTED'
);


--
-- Name: auditactionenum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.auditactionenum AS ENUM (
    'CREATE',
    'UPDATE',
    'DELETE',
    'LOGIN',
    'LOGOUT',
    'EXPORT',
    'IMPORT',
    'APPROVE',
    'REJECT'
);


--
-- Name: bonustypeenum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.bonustypeenum AS ENUM (
    'PERFORMANCE_BASED',
    'FIXED',
    'MIXED'
);


--
-- Name: budgetscenariotypeenum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.budgetscenariotypeenum AS ENUM (
    'BASE',
    'OPTIMISTIC',
    'PESSIMISTIC'
);


--
-- Name: budgetstatusenum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.budgetstatusenum AS ENUM (
    'DRAFT',
    'APPROVED'
);


--
-- Name: budgetversionstatusenum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.budgetversionstatusenum AS ENUM (
    'DRAFT',
    'IN_REVIEW',
    'REVISION_REQUESTED',
    'APPROVED',
    'REJECTED',
    'ARCHIVED'
);


--
-- Name: calculationmethodenum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.calculationmethodenum AS ENUM (
    'AVERAGE',
    'GROWTH',
    'DRIVER_BASED',
    'SEASONAL',
    'MANUAL'
);


--
-- Name: employeestatusenum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.employeestatusenum AS ENUM (
    'ACTIVE',
    'ON_VACATION',
    'ON_LEAVE',
    'FIRED'
);


--
-- Name: expensestatusenum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.expensestatusenum AS ENUM (
    'DRAFT',
    'PENDING',
    'PAID',
    'REJECTED',
    'CLOSED'
);


--
-- Name: expensetypeenum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.expensetypeenum AS ENUM (
    'OPEX',
    'CAPEX'
);


--
-- Name: kpigoalstatusenum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.kpigoalstatusenum AS ENUM (
    'DRAFT',
    'ACTIVE',
    'ACHIEVED',
    'NOT_ACHIEVED',
    'CANCELLED'
);


--
-- Name: userroleenum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.userroleenum AS ENUM (
    'ADMIN',
    'MANAGER',
    'USER'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: attachments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.attachments (
    id integer NOT NULL,
    expense_id integer NOT NULL,
    filename character varying(500) NOT NULL,
    file_path character varying(1000) NOT NULL,
    file_size integer NOT NULL,
    mime_type character varying(100),
    file_type character varying(50),
    uploaded_by character varying(255),
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: attachments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.attachments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: attachments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.attachments_id_seq OWNED BY public.attachments.id;


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    user_id integer,
    action public.auditactionenum NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id integer,
    description text,
    changes json,
    ip_address character varying(45),
    user_agent character varying(500),
    department_id integer,
    "timestamp" timestamp without time zone NOT NULL
);


--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: budget_approval_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.budget_approval_log (
    id integer NOT NULL,
    version_id integer NOT NULL,
    iteration_number integer NOT NULL,
    reviewer_name character varying(100) NOT NULL,
    reviewer_role character varying(50) NOT NULL,
    action public.approvalactionenum NOT NULL,
    decision_date timestamp without time zone NOT NULL,
    comments text,
    requested_changes json,
    next_action character varying(100),
    deadline date,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: budget_approval_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.budget_approval_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: budget_approval_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.budget_approval_log_id_seq OWNED BY public.budget_approval_log.id;


--
-- Name: budget_categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.budget_categories (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    type public.expensetypeenum NOT NULL,
    description text,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    parent_id integer,
    department_id integer NOT NULL
);


--
-- Name: budget_categories_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.budget_categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: budget_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.budget_categories_id_seq OWNED BY public.budget_categories.id;


--
-- Name: budget_plan_details; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.budget_plan_details (
    id integer NOT NULL,
    version_id integer NOT NULL,
    month integer NOT NULL,
    category_id integer NOT NULL,
    subcategory character varying(100),
    planned_amount numeric(15,2) NOT NULL,
    type public.expensetypeenum NOT NULL,
    calculation_method public.calculationmethodenum,
    calculation_params json,
    business_driver character varying(100),
    justification text,
    based_on_year integer,
    based_on_avg numeric(15,2),
    based_on_total numeric(15,2),
    growth_rate numeric(5,2),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: budget_plan_details_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.budget_plan_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: budget_plan_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.budget_plan_details_id_seq OWNED BY public.budget_plan_details.id;


--
-- Name: budget_plans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.budget_plans (
    id integer NOT NULL,
    year integer NOT NULL,
    month integer NOT NULL,
    category_id integer NOT NULL,
    planned_amount numeric(15,2) NOT NULL,
    capex_planned numeric(15,2) NOT NULL,
    opex_planned numeric(15,2) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    status public.budgetstatusenum DEFAULT 'DRAFT'::public.budgetstatusenum NOT NULL,
    department_id integer NOT NULL
);


--
-- Name: budget_plans_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.budget_plans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: budget_plans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.budget_plans_id_seq OWNED BY public.budget_plans.id;


--
-- Name: budget_scenarios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.budget_scenarios (
    id integer NOT NULL,
    year integer NOT NULL,
    scenario_name character varying(100) NOT NULL,
    scenario_type public.budgetscenariotypeenum NOT NULL,
    department_id integer NOT NULL,
    global_growth_rate numeric(5,2) DEFAULT 0 NOT NULL,
    inflation_rate numeric(5,2) DEFAULT 0 NOT NULL,
    fx_rate numeric(10,4),
    assumptions json,
    description text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by character varying(100)
);


--
-- Name: budget_scenarios_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.budget_scenarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: budget_scenarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.budget_scenarios_id_seq OWNED BY public.budget_scenarios.id;


--
-- Name: budget_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.budget_versions (
    id integer NOT NULL,
    year integer NOT NULL,
    version_number integer NOT NULL,
    version_name character varying(100),
    department_id integer NOT NULL,
    scenario_id integer,
    status public.budgetversionstatusenum DEFAULT 'DRAFT'::public.budgetversionstatusenum NOT NULL,
    created_by character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    submitted_at timestamp without time zone,
    approved_at timestamp without time zone,
    approved_by character varying(100),
    comments text,
    change_log text,
    total_amount numeric(15,2) DEFAULT 0 NOT NULL,
    total_capex numeric(15,2) DEFAULT 0 NOT NULL,
    total_opex numeric(15,2) DEFAULT 0 NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: budget_versions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.budget_versions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: budget_versions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.budget_versions_id_seq OWNED BY public.budget_versions.id;


--
-- Name: contractors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.contractors (
    id integer NOT NULL,
    name character varying(500) NOT NULL,
    short_name character varying(255),
    inn character varying(20),
    contact_info text,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    department_id integer NOT NULL
);


--
-- Name: contractors_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.contractors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: contractors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.contractors_id_seq OWNED BY public.contractors.id;


--
-- Name: dashboard_configs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dashboard_configs (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    is_default boolean NOT NULL,
    is_public boolean NOT NULL,
    config json NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    user_id integer
);


--
-- Name: dashboard_configs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dashboard_configs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dashboard_configs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dashboard_configs_id_seq OWNED BY public.dashboard_configs.id;


--
-- Name: departments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.departments (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    code character varying(50) NOT NULL,
    description text,
    is_active boolean NOT NULL,
    manager_name character varying(255),
    contact_email character varying(255),
    contact_phone character varying(50),
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    ftp_subdivision_name character varying(255)
);


--
-- Name: departments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.departments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: departments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.departments_id_seq OWNED BY public.departments.id;


--
-- Name: employee_kpi_goals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employee_kpi_goals (
    id integer NOT NULL,
    employee_id integer NOT NULL,
    goal_id integer NOT NULL,
    employee_kpi_id integer,
    year integer NOT NULL,
    month integer,
    target_value numeric(15,2),
    actual_value numeric(15,2),
    achievement_percentage numeric(5,2),
    weight numeric(5,2),
    status public.kpigoalstatusenum DEFAULT 'ACTIVE'::public.kpigoalstatusenum NOT NULL,
    notes text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: employee_kpi_goals_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.employee_kpi_goals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: employee_kpi_goals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.employee_kpi_goals_id_seq OWNED BY public.employee_kpi_goals.id;


--
-- Name: employee_kpis; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employee_kpis (
    id integer NOT NULL,
    employee_id integer NOT NULL,
    year integer NOT NULL,
    month integer NOT NULL,
    kpi_percentage numeric(5,2),
    monthly_bonus_type public.bonustypeenum DEFAULT 'PERFORMANCE_BASED'::public.bonustypeenum NOT NULL,
    quarterly_bonus_type public.bonustypeenum DEFAULT 'PERFORMANCE_BASED'::public.bonustypeenum NOT NULL,
    annual_bonus_type public.bonustypeenum DEFAULT 'PERFORMANCE_BASED'::public.bonustypeenum NOT NULL,
    monthly_bonus_base numeric(15,2) DEFAULT 0 NOT NULL,
    quarterly_bonus_base numeric(15,2) DEFAULT 0 NOT NULL,
    annual_bonus_base numeric(15,2) DEFAULT 0 NOT NULL,
    monthly_bonus_calculated numeric(15,2),
    quarterly_bonus_calculated numeric(15,2),
    annual_bonus_calculated numeric(15,2),
    monthly_bonus_fixed_part numeric(5,2),
    quarterly_bonus_fixed_part numeric(5,2),
    annual_bonus_fixed_part numeric(5,2),
    department_id integer NOT NULL,
    notes text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: employee_kpis_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.employee_kpis_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: employee_kpis_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.employee_kpis_id_seq OWNED BY public.employee_kpis.id;


--
-- Name: employees; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employees (
    id integer NOT NULL,
    full_name character varying(255) NOT NULL,
    "position" character varying(255) NOT NULL,
    employee_number character varying(50),
    hire_date date,
    fire_date date,
    status public.employeestatusenum NOT NULL,
    base_salary numeric(15,2) NOT NULL,
    department_id integer NOT NULL,
    email character varying(255),
    phone character varying(50),
    notes text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    monthly_bonus_base numeric(15,2) DEFAULT 0 NOT NULL,
    quarterly_bonus_base numeric(15,2) DEFAULT 0,
    annual_bonus_base numeric(15,2) DEFAULT 0
);


--
-- Name: employees_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.employees_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: employees_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.employees_id_seq OWNED BY public.employees.id;


--
-- Name: expenses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.expenses (
    id integer NOT NULL,
    number character varying(50) NOT NULL,
    category_id integer,
    contractor_id integer,
    organization_id integer NOT NULL,
    amount numeric(15,2) NOT NULL,
    request_date timestamp without time zone NOT NULL,
    payment_date timestamp without time zone,
    status public.expensestatusenum NOT NULL,
    is_paid boolean NOT NULL,
    is_closed boolean NOT NULL,
    comment text,
    requester character varying(255),
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    imported_from_ftp boolean DEFAULT false NOT NULL,
    needs_review boolean DEFAULT false NOT NULL,
    department_id integer NOT NULL
);


--
-- Name: expenses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.expenses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: expenses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.expenses_id_seq OWNED BY public.expenses.id;


--
-- Name: forecast_expenses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.forecast_expenses (
    id integer NOT NULL,
    category_id integer NOT NULL,
    contractor_id integer,
    organization_id integer NOT NULL,
    forecast_date date NOT NULL,
    amount numeric(15,2) NOT NULL,
    comment text,
    is_regular boolean NOT NULL,
    based_on_expense_id integer,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    department_id integer NOT NULL
);


--
-- Name: forecast_expenses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.forecast_expenses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: forecast_expenses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.forecast_expenses_id_seq OWNED BY public.forecast_expenses.id;


--
-- Name: kpi_goals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kpi_goals (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    category character varying(100),
    metric_name character varying(255),
    metric_unit character varying(50),
    target_value numeric(15,2),
    weight numeric(5,2) DEFAULT 100 NOT NULL,
    year integer NOT NULL,
    is_annual boolean DEFAULT true NOT NULL,
    status public.kpigoalstatusenum DEFAULT 'DRAFT'::public.kpigoalstatusenum NOT NULL,
    department_id integer NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: kpi_goals_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.kpi_goals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: kpi_goals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.kpi_goals_id_seq OWNED BY public.kpi_goals.id;


--
-- Name: organizations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.organizations (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    legal_name character varying(500),
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    department_id integer NOT NULL
);


--
-- Name: organizations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.organizations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: organizations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.organizations_id_seq OWNED BY public.organizations.id;


--
-- Name: payroll_actuals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payroll_actuals (
    id integer NOT NULL,
    year integer NOT NULL,
    month integer NOT NULL,
    employee_id integer NOT NULL,
    department_id integer NOT NULL,
    base_salary_paid numeric(15,2) NOT NULL,
    other_payments_paid numeric(15,2) NOT NULL,
    total_paid numeric(15,2) NOT NULL,
    payment_date date,
    expense_id integer,
    notes text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    monthly_bonus_paid numeric(15,2) DEFAULT 0 NOT NULL,
    quarterly_bonus_paid numeric(15,2) DEFAULT 0 NOT NULL,
    annual_bonus_paid numeric(15,2) DEFAULT 0 NOT NULL,
    income_tax_rate numeric(5,4) DEFAULT 0.13 NOT NULL,
    income_tax_amount numeric(15,2) DEFAULT '0'::numeric NOT NULL,
    social_tax_amount numeric(15,2) DEFAULT '0'::numeric NOT NULL
);


--
-- Name: payroll_actuals_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.payroll_actuals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payroll_actuals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.payroll_actuals_id_seq OWNED BY public.payroll_actuals.id;


--
-- Name: payroll_plans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payroll_plans (
    id integer NOT NULL,
    year integer NOT NULL,
    month integer NOT NULL,
    employee_id integer NOT NULL,
    department_id integer NOT NULL,
    base_salary numeric(15,2) NOT NULL,
    other_payments numeric(15,2) NOT NULL,
    total_planned numeric(15,2) NOT NULL,
    notes text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    monthly_bonus numeric(15,2) DEFAULT 0 NOT NULL,
    quarterly_bonus numeric(15,2) DEFAULT 0 NOT NULL,
    annual_bonus numeric(15,2) DEFAULT 0 NOT NULL
);


--
-- Name: payroll_plans_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.payroll_plans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payroll_plans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.payroll_plans_id_seq OWNED BY public.payroll_plans.id;


--
-- Name: salary_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.salary_history (
    id integer NOT NULL,
    employee_id integer NOT NULL,
    old_salary numeric(15,2),
    new_salary numeric(15,2) NOT NULL,
    effective_date date NOT NULL,
    reason text,
    notes text,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: salary_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.salary_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: salary_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.salary_history_id_seq OWNED BY public.salary_history.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    full_name character varying(255),
    hashed_password character varying(255) NOT NULL,
    role public.userroleenum DEFAULT 'USER'::public.userroleenum NOT NULL,
    is_active boolean NOT NULL,
    is_verified boolean NOT NULL,
    "position" character varying(255),
    phone character varying(50),
    last_login timestamp without time zone,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    department_id integer
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: attachments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attachments ALTER COLUMN id SET DEFAULT nextval('public.attachments_id_seq'::regclass);


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: budget_approval_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_approval_log ALTER COLUMN id SET DEFAULT nextval('public.budget_approval_log_id_seq'::regclass);


--
-- Name: budget_categories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_categories ALTER COLUMN id SET DEFAULT nextval('public.budget_categories_id_seq'::regclass);


--
-- Name: budget_plan_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_plan_details ALTER COLUMN id SET DEFAULT nextval('public.budget_plan_details_id_seq'::regclass);


--
-- Name: budget_plans id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_plans ALTER COLUMN id SET DEFAULT nextval('public.budget_plans_id_seq'::regclass);


--
-- Name: budget_scenarios id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_scenarios ALTER COLUMN id SET DEFAULT nextval('public.budget_scenarios_id_seq'::regclass);


--
-- Name: budget_versions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_versions ALTER COLUMN id SET DEFAULT nextval('public.budget_versions_id_seq'::regclass);


--
-- Name: contractors id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contractors ALTER COLUMN id SET DEFAULT nextval('public.contractors_id_seq'::regclass);


--
-- Name: dashboard_configs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dashboard_configs ALTER COLUMN id SET DEFAULT nextval('public.dashboard_configs_id_seq'::regclass);


--
-- Name: departments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments ALTER COLUMN id SET DEFAULT nextval('public.departments_id_seq'::regclass);


--
-- Name: employee_kpi_goals id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_kpi_goals ALTER COLUMN id SET DEFAULT nextval('public.employee_kpi_goals_id_seq'::regclass);


--
-- Name: employee_kpis id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_kpis ALTER COLUMN id SET DEFAULT nextval('public.employee_kpis_id_seq'::regclass);


--
-- Name: employees id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees ALTER COLUMN id SET DEFAULT nextval('public.employees_id_seq'::regclass);


--
-- Name: expenses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses ALTER COLUMN id SET DEFAULT nextval('public.expenses_id_seq'::regclass);


--
-- Name: forecast_expenses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.forecast_expenses ALTER COLUMN id SET DEFAULT nextval('public.forecast_expenses_id_seq'::regclass);


--
-- Name: kpi_goals id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kpi_goals ALTER COLUMN id SET DEFAULT nextval('public.kpi_goals_id_seq'::regclass);


--
-- Name: organizations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations ALTER COLUMN id SET DEFAULT nextval('public.organizations_id_seq'::regclass);


--
-- Name: payroll_actuals id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_actuals ALTER COLUMN id SET DEFAULT nextval('public.payroll_actuals_id_seq'::regclass);


--
-- Name: payroll_plans id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_plans ALTER COLUMN id SET DEFAULT nextval('public.payroll_plans_id_seq'::regclass);


--
-- Name: salary_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.salary_history ALTER COLUMN id SET DEFAULT nextval('public.salary_history_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
ac976a594e2f
\.


--
-- Data for Name: attachments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.attachments (id, expense_id, filename, file_path, file_size, mime_type, file_type, uploaded_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.audit_logs (id, user_id, action, entity_type, entity_id, description, changes, ip_address, user_agent, department_id, "timestamp") FROM stdin;
1	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	1	2025-10-25 16:04:59.128589
2	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	1	2025-10-25 16:05:14.745209
3	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	1	2025-10-25 16:10:06.711822
36	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	1	2025-10-25 16:15:55.645995
37	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	python-requests/2.32.3	1	2025-10-25 16:18:13.122596
38	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	1	2025-10-25 16:19:47.377683
39	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	python-requests/2.32.3	1	2025-10-25 16:20:01.909931
40	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	1	2025-10-25 16:20:38.115302
41	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	1	2025-10-25 16:31:07.695541
42	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	1	2025-10-25 16:36:29.409259
43	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	1	2025-10-25 16:36:51.110021
44	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	1	2025-10-25 16:48:02.00946
45	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	1	2025-10-25 16:48:12.93768
46	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	1	2025-10-25 16:52:35.961371
47	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	1	2025-10-25 19:46:12.642738
48	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	1	2025-10-25 20:03:38.620313
49	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	2	2025-10-25 20:23:20.299996
50	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	2	2025-10-26 08:34:39.221673
51	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	2	2025-10-26 08:45:06.302284
52	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	2	2025-10-26 08:46:26.953454
53	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	2	2025-10-26 19:40:55.384209
54	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	curl/8.7.1	2	2025-10-27 07:16:42.073189
55	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	curl/8.7.1	2	2025-10-27 07:33:27.876444
56	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	curl/8.7.1	2	2025-10-27 07:40:38.877505
57	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	2	2025-10-27 19:00:39.354945
58	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	2	2025-10-27 19:14:55.73238
59	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	2	2025-10-27 21:07:16.471889
60	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	2	2025-10-28 07:52:27.06562
61	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	2	2025-10-28 14:02:29.135356
62	1	LOGIN	User	1	User admin logged in	null	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15	2	2025-10-28 22:50:34.62945
\.


--
-- Data for Name: budget_approval_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.budget_approval_log (id, version_id, iteration_number, reviewer_name, reviewer_role, action, decision_date, comments, requested_changes, next_action, deadline, created_at) FROM stdin;
\.


--
-- Data for Name: budget_categories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.budget_categories (id, name, type, description, is_active, created_at, updated_at, parent_id, department_id) FROM stdin;
15	1с (аутсорс)	CAPEX	\N	t	2025-10-25 17:03:56.475668	2025-10-26 08:48:49.570134	43	2
8	1с(лицензии)	OPEX	123	t	2025-10-25 17:03:56.422784	2025-10-25 20:44:53.356449	41	2
42	(Группа) Техника	CAPEX	\N	t	2025-10-25 20:57:27.849751	2025-10-25 20:57:27.849755	\N	2
41	(Группа) Покупка ПО	CAPEX	1	t	2025-10-25 20:44:38.610228	2025-10-25 20:57:32.264716	\N	2
30	Техника ВЭД	OPEX	\N	t	2025-10-25 17:03:56.556353	2025-10-25 20:57:46.668027	42	2
43	(Группа) Аутсорс	CAPEX	\N	t	2025-10-26 08:33:38.637193	2025-10-26 08:33:38.6372	\N	2
14	Битрикс 24 Разработка	OPEX	\N	t	2025-10-25 17:03:56.470013	2025-10-26 08:33:52.999247	43	2
9	Битрикс24(лицензии)	OPEX	\N	t	2025-10-25 17:03:56.433476	2025-10-26 08:48:13.789147	41	2
10	Интегарции телефонии чатов и пр	OPEX	\N	t	2025-10-25 17:03:56.442665	2025-10-26 08:48:20.185819	41	2
11	Почтовый Сервер	OPEX	\N	t	2025-10-25 17:03:56.450928	2025-10-26 08:48:25.565267	43	2
12	Связь (телефон/интернет)	OPEX	\N	t	2025-10-25 17:03:56.457965	2025-10-26 08:48:32.717372	41	2
13	Битрикс 24(настройка)	CAPEX	\N	t	2025-10-25 17:03:56.464157	2025-10-26 08:48:38.583011	43	2
16	Аналитика данных	OPEX	\N	t	2025-10-25 17:03:56.481417	2025-10-26 08:49:03.362535	43	2
17	Приложение визитов(разработка)	CAPEX	\N	t	2025-10-25 17:03:56.486087	2025-10-26 08:49:10.656575	43	2
18	Ремонты и тех обслуживание	OPEX	\N	t	2025-10-25 17:03:56.491415	2025-10-26 08:49:23.422232	42	2
19	Обслуживание оргтехники	CAPEX	\N	t	2025-10-25 17:03:56.496224	2025-10-26 08:49:32.035196	42	2
20	Заправка картриджей	OPEX	\N	t	2025-10-25 17:03:56.501971	2025-10-26 08:49:42.452761	42	2
21	Расходные материалы	OPEX	\N	t	2025-10-25 17:03:56.507808	2025-10-26 08:49:50.855268	42	2
22	Сервер 1с	CAPEX	\N	t	2025-10-25 17:03:56.513345	2025-10-26 08:49:58.525813	42	2
23	Хостинг CRM	OPEX	\N	t	2025-10-25 17:03:56.518706	2025-10-26 08:52:13.306292	42	2
24	Новая квартира для серверов (Колокейшн)	OPEX	\N	t	2025-10-25 17:03:56.52355	2025-10-26 08:52:27.271189	42	2
25	Реновация техники	CAPEX	\N	t	2025-10-25 17:03:56.528014	2025-10-26 08:52:38.08768	42	2
26	Покупка принтеров и прочей орг техники(обновление)	CAPEX	\N	t	2025-10-25 17:03:56.53325	2025-10-26 08:52:50.412154	42	2
28	Техника Логистика	CAPEX	\N	t	2025-10-25 17:03:56.544392	2025-10-26 08:53:09.648653	42	2
35	Техника отдел маркетинга	CAPEX	\N	t	2025-10-25 17:03:56.581235	2025-10-26 08:54:08.599177	42	2
29	Техника Склад	CAPEX	\N	t	2025-10-25 17:03:56.550732	2025-10-26 08:54:21.695745	42	2
31	Техника Юр. отдел	CAPEX	\N	t	2025-10-25 17:03:56.560755	2025-10-26 08:54:31.681565	42	2
32	Техника Москва	CAPEX	\N	t	2025-10-25 17:03:56.565738	2025-10-26 08:54:42.879736	42	2
33	Техника Сервис	CAPEX	\N	t	2025-10-25 17:03:56.570284	2025-10-26 08:54:50.332889	42	2
34	Техника ОП СПб	OPEX	\N	t	2025-10-25 17:03:56.576204	2025-10-26 08:54:59.154653	42	2
44	(Группа) Риски	CAPEX	\N	t	2025-10-26 08:55:20.668107	2025-10-26 08:55:20.668114	\N	2
36	Непредвиденные расходы и риски	CAPEX	\N	t	2025-10-25 17:03:56.586114	2025-10-26 08:55:30.299835	44	2
27	Техника Краснодар	CAPEX	\N	t	2025-10-25 17:03:56.538375	2025-10-26 19:12:45.707852	42	2
45	Разработки	CAPEX	\N	t	2025-10-27 08:57:34.69995	2025-10-27 08:57:34.699957	43	2
\.


--
-- Data for Name: budget_plan_details; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.budget_plan_details (id, version_id, month, category_id, subcategory, planned_amount, type, calculation_method, calculation_params, business_driver, justification, based_on_year, based_on_avg, based_on_total, growth_rate, created_at, updated_at) FROM stdin;
4	4	1	15	\N	1000.00	CAPEX	\N	null	\N	\N	\N	\N	\N	\N	2025-10-27 14:31:27.496375	2025-10-27 14:31:27.496378
\.


--
-- Data for Name: budget_plans; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.budget_plans (id, year, month, category_id, planned_amount, capex_planned, opex_planned, created_at, updated_at, status, department_id) FROM stdin;
375	2025	4	8	60000.00	0.00	60000.00	2025-10-25 17:04:38.727938	2025-10-25 17:04:38.727942	APPROVED	2
376	2025	5	9	50000.00	0.00	50000.00	2025-10-25 17:04:38.727944	2025-10-25 17:04:38.727944	APPROVED	2
377	2025	9	9	120000.00	0.00	120000.00	2025-10-25 17:04:38.727945	2025-10-25 17:04:38.727946	APPROVED	2
378	2025	3	10	15000.00	0.00	15000.00	2025-10-25 17:04:38.727947	2025-10-25 17:04:38.727948	APPROVED	2
379	2025	4	10	15000.00	0.00	15000.00	2025-10-25 17:04:38.727949	2025-10-25 17:04:38.727949	APPROVED	2
380	2025	5	10	15000.00	0.00	15000.00	2025-10-25 17:04:38.72795	2025-10-25 17:04:38.727951	APPROVED	2
381	2025	6	10	15000.00	0.00	15000.00	2025-10-25 17:04:38.727951	2025-10-25 17:04:38.727952	APPROVED	2
382	2025	7	10	15000.00	0.00	15000.00	2025-10-25 17:04:38.727953	2025-10-25 17:04:38.727953	APPROVED	2
383	2025	8	10	15000.00	0.00	15000.00	2025-10-25 17:04:38.727954	2025-10-25 17:04:38.727955	APPROVED	2
384	2025	9	10	15000.00	0.00	15000.00	2025-10-25 17:04:38.727955	2025-10-25 17:04:38.727956	APPROVED	2
385	2025	10	10	15000.00	0.00	15000.00	2025-10-25 17:04:38.727957	2025-10-25 17:04:38.727957	APPROVED	2
386	2025	11	10	15000.00	0.00	15000.00	2025-10-25 17:04:38.727958	2025-10-25 17:04:38.727959	APPROVED	2
387	2025	12	10	15000.00	0.00	15000.00	2025-10-25 17:04:38.72796	2025-10-25 17:04:38.72796	APPROVED	2
388	2025	1	11	10000.00	0.00	10000.00	2025-10-25 17:04:38.727961	2025-10-25 17:04:38.727962	APPROVED	2
389	2025	2	11	10000.00	0.00	10000.00	2025-10-25 17:04:38.727962	2025-10-25 17:04:38.727963	APPROVED	2
390	2025	3	11	10000.00	0.00	10000.00	2025-10-25 17:04:38.727964	2025-10-25 17:04:38.727964	APPROVED	2
391	2025	4	11	10000.00	0.00	10000.00	2025-10-25 17:04:38.727965	2025-10-25 17:04:38.727965	APPROVED	2
392	2025	5	11	10000.00	0.00	10000.00	2025-10-25 17:04:38.727966	2025-10-25 17:04:38.727967	APPROVED	2
393	2025	6	11	10000.00	0.00	10000.00	2025-10-25 17:04:38.727967	2025-10-25 17:04:38.727968	APPROVED	2
394	2025	7	11	10000.00	0.00	10000.00	2025-10-25 17:04:38.727969	2025-10-25 17:04:38.727969	APPROVED	2
395	2025	8	11	10000.00	0.00	10000.00	2025-10-25 17:04:38.72797	2025-10-25 17:04:38.727971	APPROVED	2
396	2025	9	11	10000.00	0.00	10000.00	2025-10-25 17:04:38.727971	2025-10-25 17:04:38.727972	APPROVED	2
397	2025	10	11	10000.00	0.00	10000.00	2025-10-25 17:04:38.727973	2025-10-25 17:04:38.727973	APPROVED	2
398	2025	11	11	10000.00	0.00	10000.00	2025-10-25 17:04:38.727974	2025-10-25 17:04:38.727975	APPROVED	2
399	2025	12	11	10000.00	0.00	10000.00	2025-10-25 17:04:38.727975	2025-10-25 17:04:38.727976	APPROVED	2
400	2025	1	12	150000.00	0.00	150000.00	2025-10-25 17:04:38.727977	2025-10-25 17:04:38.727977	APPROVED	2
401	2025	2	12	150000.00	0.00	150000.00	2025-10-25 17:04:38.727978	2025-10-25 17:04:38.727979	APPROVED	2
402	2025	3	12	150000.00	0.00	150000.00	2025-10-25 17:04:38.727979	2025-10-25 17:04:38.72798	APPROVED	2
403	2025	4	12	150000.00	0.00	150000.00	2025-10-25 17:04:38.727981	2025-10-25 17:04:38.727981	APPROVED	2
404	2025	5	12	200000.00	0.00	200000.00	2025-10-25 17:04:38.727982	2025-10-25 17:04:38.727983	APPROVED	2
405	2025	6	12	200000.00	0.00	200000.00	2025-10-25 17:04:38.727983	2025-10-25 17:04:38.727984	APPROVED	2
406	2025	7	12	200000.00	0.00	200000.00	2025-10-25 17:04:38.727985	2025-10-25 17:04:38.727985	APPROVED	2
407	2025	8	12	200000.00	0.00	200000.00	2025-10-25 17:04:38.727986	2025-10-25 17:04:38.727987	APPROVED	2
408	2025	9	12	200000.00	0.00	200000.00	2025-10-25 17:04:38.727987	2025-10-25 17:04:38.727988	APPROVED	2
409	2025	10	12	200000.00	0.00	200000.00	2025-10-25 17:04:38.727989	2025-10-25 17:04:38.727989	APPROVED	2
410	2025	11	12	200000.00	0.00	200000.00	2025-10-25 17:04:38.72799	2025-10-25 17:04:38.727991	APPROVED	2
411	2025	12	12	200000.00	0.00	200000.00	2025-10-25 17:04:38.727991	2025-10-25 17:04:38.727992	APPROVED	2
412	2025	1	13	25000.00	0.00	25000.00	2025-10-25 17:04:38.727993	2025-10-25 17:04:38.727993	APPROVED	2
413	2025	2	13	25000.00	0.00	25000.00	2025-10-25 17:04:38.727994	2025-10-25 17:04:38.727995	APPROVED	2
414	2025	3	13	25000.00	0.00	25000.00	2025-10-25 17:04:38.727995	2025-10-25 17:04:38.727996	APPROVED	2
415	2025	4	13	25000.00	0.00	25000.00	2025-10-25 17:04:38.727997	2025-10-25 17:04:38.727997	APPROVED	2
416	2025	5	13	25000.00	0.00	25000.00	2025-10-25 17:04:38.727998	2025-10-25 17:04:38.727999	APPROVED	2
417	2025	6	13	25000.00	0.00	25000.00	2025-10-25 17:04:38.727999	2025-10-25 17:04:38.728	APPROVED	2
418	2025	7	13	25000.00	0.00	25000.00	2025-10-25 17:04:38.728001	2025-10-25 17:04:38.728001	APPROVED	2
419	2025	8	13	25000.00	0.00	25000.00	2025-10-25 17:04:38.728002	2025-10-25 17:04:38.728003	APPROVED	2
420	2025	9	13	25000.00	0.00	25000.00	2025-10-25 17:04:38.728003	2025-10-25 17:04:38.728004	APPROVED	2
421	2025	10	13	25000.00	0.00	25000.00	2025-10-25 17:04:38.728005	2025-10-25 17:04:38.728005	APPROVED	2
422	2025	11	13	25000.00	0.00	25000.00	2025-10-25 17:04:38.728006	2025-10-25 17:04:38.728007	APPROVED	2
423	2025	12	13	25000.00	0.00	25000.00	2025-10-25 17:04:38.728007	2025-10-25 17:04:38.728008	APPROVED	2
424	2025	3	14	100000.00	0.00	100000.00	2025-10-25 17:04:38.728009	2025-10-25 17:04:38.728009	APPROVED	2
425	2025	4	14	200000.00	0.00	200000.00	2025-10-25 17:04:38.72801	2025-10-25 17:04:38.728011	APPROVED	2
426	2025	5	14	150000.00	0.00	150000.00	2025-10-25 17:04:38.728011	2025-10-25 17:04:38.728012	APPROVED	2
427	2025	6	14	200000.00	0.00	200000.00	2025-10-25 17:04:38.728013	2025-10-25 17:04:38.728013	APPROVED	2
428	2025	7	14	100000.00	0.00	100000.00	2025-10-25 17:04:38.728014	2025-10-25 17:04:38.728015	APPROVED	2
429	2025	8	14	200000.00	0.00	200000.00	2025-10-25 17:04:38.728015	2025-10-25 17:04:38.728016	APPROVED	2
430	2025	9	14	150000.00	0.00	150000.00	2025-10-25 17:04:38.728017	2025-10-25 17:04:38.728017	APPROVED	2
431	2025	10	14	150000.00	0.00	150000.00	2025-10-25 17:04:38.728018	2025-10-25 17:04:38.728019	APPROVED	2
432	2025	4	15	100000.00	0.00	100000.00	2025-10-25 17:04:38.728019	2025-10-25 17:04:38.72802	APPROVED	2
433	2025	6	15	100000.00	0.00	100000.00	2025-10-25 17:04:38.728021	2025-10-25 17:04:38.728021	APPROVED	2
434	2025	9	15	200000.00	0.00	200000.00	2025-10-25 17:04:38.728022	2025-10-25 17:04:38.728023	APPROVED	2
435	2025	3	16	40000.00	0.00	40000.00	2025-10-25 17:04:38.728023	2025-10-25 17:04:38.728024	APPROVED	2
436	2025	4	16	40000.00	0.00	40000.00	2025-10-25 17:04:38.728025	2025-10-25 17:04:38.728025	APPROVED	2
437	2025	5	16	40000.00	0.00	40000.00	2025-10-25 17:04:38.728026	2025-10-25 17:04:38.728027	APPROVED	2
438	2025	6	16	40000.00	0.00	40000.00	2025-10-25 17:04:38.728027	2025-10-25 17:04:38.728028	APPROVED	2
439	2025	7	16	40000.00	0.00	40000.00	2025-10-25 17:04:38.728029	2025-10-25 17:04:38.728029	APPROVED	2
440	2025	8	16	40000.00	0.00	40000.00	2025-10-25 17:04:38.72803	2025-10-25 17:04:38.728031	APPROVED	2
441	2025	9	16	40000.00	0.00	40000.00	2025-10-25 17:04:38.728031	2025-10-25 17:04:38.728032	APPROVED	2
442	2025	10	16	40000.00	0.00	40000.00	2025-10-25 17:04:38.728033	2025-10-25 17:04:38.728033	APPROVED	2
443	2025	11	16	40000.00	0.00	40000.00	2025-10-25 17:04:38.728034	2025-10-25 17:04:38.728035	APPROVED	2
444	2025	12	16	40000.00	0.00	40000.00	2025-10-25 17:04:38.728035	2025-10-25 17:04:38.728036	APPROVED	2
445	2025	4	17	150000.00	0.00	150000.00	2025-10-25 17:04:38.728037	2025-10-25 17:04:38.728037	APPROVED	2
446	2025	5	17	200000.00	0.00	200000.00	2025-10-25 17:04:38.728038	2025-10-25 17:04:38.728039	APPROVED	2
447	2025	6	17	150000.00	0.00	150000.00	2025-10-25 17:04:38.728039	2025-10-25 17:04:38.72804	APPROVED	2
448	2025	1	18	60000.00	0.00	60000.00	2025-10-25 17:04:38.728041	2025-10-25 17:04:38.728041	APPROVED	2
449	2025	2	18	60000.00	0.00	60000.00	2025-10-25 17:04:38.728042	2025-10-25 17:04:38.728043	APPROVED	2
450	2025	3	18	60000.00	0.00	60000.00	2025-10-25 17:04:38.728043	2025-10-25 17:04:38.728044	APPROVED	2
451	2025	4	18	60000.00	0.00	60000.00	2025-10-25 17:04:38.728045	2025-10-25 17:04:38.728045	APPROVED	2
452	2025	5	18	60000.00	0.00	60000.00	2025-10-25 17:04:38.728046	2025-10-25 17:04:38.728047	APPROVED	2
453	2025	6	18	60000.00	0.00	60000.00	2025-10-25 17:04:38.728047	2025-10-25 17:04:38.728048	APPROVED	2
454	2025	7	18	60000.00	0.00	60000.00	2025-10-25 17:04:38.728049	2025-10-25 17:04:38.728049	APPROVED	2
455	2025	8	18	60000.00	0.00	60000.00	2025-10-25 17:04:38.72805	2025-10-25 17:04:38.728051	APPROVED	2
456	2025	9	18	60000.00	0.00	60000.00	2025-10-25 17:04:38.728051	2025-10-25 17:04:38.728052	APPROVED	2
457	2025	10	18	60000.00	0.00	60000.00	2025-10-25 17:04:38.728053	2025-10-25 17:04:38.728053	APPROVED	2
458	2025	11	18	60000.00	0.00	60000.00	2025-10-25 17:04:38.728054	2025-10-25 17:04:38.728054	APPROVED	2
459	2025	12	18	60000.00	0.00	60000.00	2025-10-25 17:04:38.728055	2025-10-25 17:04:38.728056	APPROVED	2
460	2025	2	19	15000.00	0.00	15000.00	2025-10-25 17:04:38.728056	2025-10-25 17:04:38.728057	APPROVED	2
461	2025	3	19	15000.00	0.00	15000.00	2025-10-25 17:04:38.728058	2025-10-25 17:04:38.728058	APPROVED	2
462	2025	4	19	15000.00	0.00	15000.00	2025-10-25 17:04:38.728059	2025-10-25 17:04:38.72806	APPROVED	2
463	2025	5	19	15000.00	0.00	15000.00	2025-10-25 17:04:38.72806	2025-10-25 17:04:38.728061	APPROVED	2
464	2025	6	19	15000.00	0.00	15000.00	2025-10-25 17:04:38.728062	2025-10-25 17:04:38.728062	APPROVED	2
465	2025	7	19	15000.00	0.00	15000.00	2025-10-25 17:04:38.728063	2025-10-25 17:04:38.728064	APPROVED	2
466	2025	8	19	15000.00	0.00	15000.00	2025-10-25 17:04:38.728064	2025-10-25 17:04:38.728065	APPROVED	2
467	2025	9	19	15000.00	0.00	15000.00	2025-10-25 17:04:38.728066	2025-10-25 17:04:38.728066	APPROVED	2
468	2025	10	19	15000.00	0.00	15000.00	2025-10-25 17:04:38.728067	2025-10-25 17:04:38.728068	APPROVED	2
469	2025	11	19	15000.00	0.00	15000.00	2025-10-25 17:04:38.728068	2025-10-25 17:04:38.728069	APPROVED	2
470	2025	12	19	15000.00	0.00	15000.00	2025-10-25 17:04:38.72807	2025-10-25 17:04:38.72807	APPROVED	2
471	2025	2	20	20000.00	0.00	20000.00	2025-10-25 17:04:38.728071	2025-10-25 17:04:38.728072	APPROVED	2
472	2025	3	20	20000.00	0.00	20000.00	2025-10-25 17:04:38.728073	2025-10-25 17:04:38.728073	APPROVED	2
473	2025	4	20	20000.00	0.00	20000.00	2025-10-25 17:04:38.728074	2025-10-25 17:04:38.728075	APPROVED	2
474	2025	5	20	20000.00	0.00	20000.00	2025-10-25 17:04:38.728075	2025-10-25 17:04:38.728076	APPROVED	2
475	2025	6	20	20000.00	0.00	20000.00	2025-10-25 17:04:38.728077	2025-10-25 17:04:38.728077	APPROVED	2
476	2025	7	20	20000.00	0.00	20000.00	2025-10-25 17:04:38.728078	2025-10-25 17:04:38.728079	APPROVED	2
477	2025	8	20	20000.00	0.00	20000.00	2025-10-25 17:04:38.728079	2025-10-25 17:04:38.72808	APPROVED	2
478	2025	9	20	20000.00	0.00	20000.00	2025-10-25 17:04:38.728081	2025-10-25 17:04:38.728081	APPROVED	2
479	2025	10	20	20000.00	0.00	20000.00	2025-10-25 17:04:38.728082	2025-10-25 17:04:38.728083	APPROVED	2
480	2025	11	20	20000.00	0.00	20000.00	2025-10-25 17:04:38.728083	2025-10-25 17:04:38.728084	APPROVED	2
481	2025	12	20	20000.00	0.00	20000.00	2025-10-25 17:04:38.728085	2025-10-25 17:04:38.728085	APPROVED	2
482	2025	1	21	30000.00	0.00	30000.00	2025-10-25 17:04:38.728086	2025-10-25 17:04:38.728087	APPROVED	2
483	2025	2	21	30000.00	0.00	30000.00	2025-10-25 17:04:38.728088	2025-10-25 17:04:38.728088	APPROVED	2
484	2025	3	21	30000.00	0.00	30000.00	2025-10-25 17:04:38.728089	2025-10-25 17:04:38.728089	APPROVED	2
485	2025	4	21	30000.00	0.00	30000.00	2025-10-25 17:04:38.72809	2025-10-25 17:04:38.728091	APPROVED	2
486	2025	5	21	30000.00	0.00	30000.00	2025-10-25 17:04:38.728091	2025-10-25 17:04:38.728092	APPROVED	2
487	2025	6	21	30000.00	0.00	30000.00	2025-10-25 17:04:38.728093	2025-10-25 17:04:38.728098	APPROVED	2
488	2025	7	21	30000.00	0.00	30000.00	2025-10-25 17:04:38.728105	2025-10-25 17:04:38.728107	APPROVED	2
489	2025	8	21	30000.00	0.00	30000.00	2025-10-25 17:04:38.728108	2025-10-25 17:04:38.728108	APPROVED	2
490	2025	9	21	30000.00	0.00	30000.00	2025-10-25 17:04:38.728109	2025-10-25 17:04:38.72811	APPROVED	2
491	2025	10	21	30000.00	0.00	30000.00	2025-10-25 17:04:38.728111	2025-10-25 17:04:38.728111	APPROVED	2
492	2025	11	21	30000.00	0.00	30000.00	2025-10-25 17:04:38.728112	2025-10-25 17:04:38.728113	APPROVED	2
493	2025	12	21	30000.00	0.00	30000.00	2025-10-25 17:04:38.728114	2025-10-25 17:04:38.728114	APPROVED	2
494	2025	5	22	500000.00	0.00	500000.00	2025-10-25 17:04:38.728115	2025-10-25 17:04:38.728116	APPROVED	2
495	2025	6	22	850000.00	0.00	850000.00	2025-10-25 17:04:38.728117	2025-10-25 17:04:38.728117	APPROVED	2
496	2025	12	23	20000.00	0.00	20000.00	2025-10-25 17:04:38.728118	2025-10-25 17:04:38.728119	APPROVED	2
497	2025	3	24	50000.00	0.00	50000.00	2025-10-25 17:04:38.728119	2025-10-25 17:04:38.72812	APPROVED	2
498	2025	4	24	50000.00	0.00	50000.00	2025-10-25 17:04:38.728121	2025-10-25 17:04:38.728122	APPROVED	2
499	2025	5	24	50000.00	0.00	50000.00	2025-10-25 17:04:38.728123	2025-10-25 17:04:38.728123	APPROVED	2
500	2025	6	24	50000.00	0.00	50000.00	2025-10-25 17:04:38.728124	2025-10-25 17:04:38.728125	APPROVED	2
501	2025	7	24	50000.00	0.00	50000.00	2025-10-25 17:04:38.728125	2025-10-25 17:04:38.728126	APPROVED	2
502	2025	8	24	50000.00	0.00	50000.00	2025-10-25 17:04:38.728127	2025-10-25 17:04:38.728128	APPROVED	2
503	2025	9	24	50000.00	0.00	50000.00	2025-10-25 17:04:38.728128	2025-10-25 17:04:38.728129	APPROVED	2
504	2025	10	24	50000.00	0.00	50000.00	2025-10-25 17:04:38.72813	2025-10-25 17:04:38.728131	APPROVED	2
505	2025	11	24	50000.00	0.00	50000.00	2025-10-25 17:04:38.728131	2025-10-25 17:04:38.728132	APPROVED	2
506	2025	12	24	50000.00	0.00	50000.00	2025-10-25 17:04:38.728133	2025-10-25 17:04:38.728133	APPROVED	2
507	2025	2	25	200000.00	0.00	200000.00	2025-10-25 17:04:38.728134	2025-10-25 17:04:38.728135	APPROVED	2
508	2025	4	25	150000.00	0.00	150000.00	2025-10-25 17:04:38.728135	2025-10-25 17:04:38.728136	APPROVED	2
509	2025	7	25	250000.00	0.00	250000.00	2025-10-25 17:04:38.728137	2025-10-25 17:04:38.728138	APPROVED	2
510	2025	10	25	150000.00	0.00	150000.00	2025-10-25 17:04:38.728138	2025-10-25 17:04:38.728139	APPROVED	2
511	2025	12	25	150000.00	0.00	150000.00	2025-10-25 17:04:38.72814	2025-10-25 17:04:38.72814	APPROVED	2
512	2025	4	26	100000.00	0.00	100000.00	2025-10-25 17:04:38.728141	2025-10-25 17:04:38.728142	APPROVED	2
513	2025	5	26	100000.00	0.00	100000.00	2025-10-25 17:04:38.728143	2025-10-25 17:04:38.728143	APPROVED	2
514	2025	6	26	100000.00	0.00	100000.00	2025-10-25 17:04:38.728144	2025-10-25 17:04:38.728145	APPROVED	2
515	2025	7	26	100000.00	0.00	100000.00	2025-10-25 17:04:38.728145	2025-10-25 17:04:38.728146	APPROVED	2
516	2025	8	26	100000.00	0.00	100000.00	2025-10-25 17:04:38.728147	2025-10-25 17:04:38.728147	APPROVED	2
517	2025	9	26	100000.00	0.00	100000.00	2025-10-25 17:04:38.728148	2025-10-25 17:04:38.728149	APPROVED	2
518	2025	10	26	100000.00	0.00	100000.00	2025-10-25 17:04:38.72815	2025-10-25 17:04:38.72815	APPROVED	2
519	2025	11	26	100000.00	0.00	100000.00	2025-10-25 17:04:38.728151	2025-10-25 17:04:38.728152	APPROVED	2
520	2025	12	26	100000.00	0.00	100000.00	2025-10-25 17:04:38.728152	2025-10-25 17:04:38.728153	APPROVED	2
521	2025	2	27	100000.00	0.00	100000.00	2025-10-25 17:04:38.728154	2025-10-25 17:04:38.728155	APPROVED	2
522	2025	3	27	180000.00	0.00	180000.00	2025-10-25 17:04:38.728155	2025-10-25 17:04:38.728156	APPROVED	2
523	2025	6	27	150000.00	0.00	150000.00	2025-10-25 17:04:38.728157	2025-10-25 17:04:38.728157	APPROVED	2
524	2025	7	27	180000.00	0.00	180000.00	2025-10-25 17:04:38.728158	2025-10-25 17:04:38.728159	APPROVED	2
525	2025	1	28	20000.00	0.00	20000.00	2025-10-25 17:04:38.728159	2025-10-25 17:04:38.72816	APPROVED	2
526	2025	2	28	20000.00	0.00	20000.00	2025-10-25 17:04:38.728161	2025-10-25 17:04:38.728161	APPROVED	2
527	2025	3	28	20000.00	0.00	20000.00	2025-10-25 17:04:38.728162	2025-10-25 17:04:38.728163	APPROVED	2
528	2025	4	28	20000.00	0.00	20000.00	2025-10-25 17:04:38.728164	2025-10-25 17:04:38.728164	APPROVED	2
529	2025	1	29	200000.00	0.00	200000.00	2025-10-25 17:04:38.728165	2025-10-25 17:04:38.728166	APPROVED	2
530	2025	1	30	70000.00	0.00	70000.00	2025-10-25 17:04:38.728167	2025-10-25 17:04:38.728167	APPROVED	2
531	2025	2	30	70000.00	0.00	70000.00	2025-10-25 17:04:38.728168	2025-10-25 17:04:38.728169	APPROVED	2
532	2025	1	31	70000.00	0.00	70000.00	2025-10-25 17:04:38.728169	2025-10-25 17:04:38.72817	APPROVED	2
533	2025	1	32	20000.00	0.00	20000.00	2025-10-25 17:04:38.728171	2025-10-25 17:04:38.728171	APPROVED	2
534	2025	2	32	170000.00	0.00	170000.00	2025-10-25 17:04:38.728172	2025-10-25 17:04:38.728173	APPROVED	2
535	2025	3	32	120000.00	0.00	120000.00	2025-10-25 17:04:38.728174	2025-10-25 17:04:38.728174	APPROVED	2
536	2025	4	32	20000.00	0.00	20000.00	2025-10-25 17:04:38.728175	2025-10-25 17:04:38.728176	APPROVED	2
537	2025	5	32	20000.00	0.00	20000.00	2025-10-25 17:04:38.728176	2025-10-25 17:04:38.728177	APPROVED	2
538	2025	6	32	20000.00	0.00	20000.00	2025-10-25 17:04:38.728178	2025-10-25 17:04:38.728179	APPROVED	2
539	2025	7	32	120000.00	0.00	120000.00	2025-10-25 17:04:38.728179	2025-10-25 17:04:38.72818	APPROVED	2
540	2025	8	32	70000.00	0.00	70000.00	2025-10-25 17:04:38.728181	2025-10-25 17:04:38.728181	APPROVED	2
541	2025	9	32	20000.00	0.00	20000.00	2025-10-25 17:04:38.728182	2025-10-25 17:04:38.728183	APPROVED	2
542	2025	10	32	120000.00	0.00	120000.00	2025-10-25 17:04:38.728183	2025-10-25 17:04:38.728184	APPROVED	2
543	2025	11	32	20000.00	0.00	20000.00	2025-10-25 17:04:38.728185	2025-10-25 17:04:38.728185	APPROVED	2
544	2025	12	32	20000.00	0.00	20000.00	2025-10-25 17:04:38.728186	2025-10-25 17:04:38.728187	APPROVED	2
545	2025	1	33	80000.00	0.00	80000.00	2025-10-25 17:04:38.728188	2025-10-25 17:04:38.728188	APPROVED	2
546	2025	1	34	70000.00	0.00	70000.00	2025-10-25 17:04:38.728189	2025-10-25 17:04:38.72819	APPROVED	2
547	2025	3	34	70000.00	0.00	70000.00	2025-10-25 17:04:38.728191	2025-10-25 17:04:38.728191	APPROVED	2
548	2025	4	34	100000.00	0.00	100000.00	2025-10-25 17:04:38.728192	2025-10-25 17:04:38.728193	APPROVED	2
549	2025	7	34	70000.00	0.00	70000.00	2025-10-25 17:04:38.728193	2025-10-25 17:04:38.728194	APPROVED	2
550	2025	9	34	70000.00	0.00	70000.00	2025-10-25 17:04:38.728195	2025-10-25 17:04:38.728196	APPROVED	2
551	2025	11	34	70000.00	0.00	70000.00	2025-10-25 17:04:38.728197	2025-10-25 17:04:38.728197	APPROVED	2
552	2025	12	34	70000.00	0.00	70000.00	2025-10-25 17:04:38.728198	2025-10-25 17:04:38.728199	APPROVED	2
553	2025	1	35	110000.00	0.00	110000.00	2025-10-25 17:04:38.728199	2025-10-25 17:04:38.7282	APPROVED	2
554	2025	2	35	290000.00	0.00	290000.00	2025-10-25 17:04:38.728201	2025-10-25 17:04:38.728202	APPROVED	2
555	2025	7	35	80000.00	0.00	80000.00	2025-10-25 17:04:38.728202	2025-10-25 17:04:38.728203	APPROVED	2
556	2025	4	36	210000.00	0.00	210000.00	2025-10-25 17:04:38.728204	2025-10-25 17:04:38.728204	APPROVED	2
557	2025	5	36	290000.00	0.00	290000.00	2025-10-25 17:04:38.728205	2025-10-25 17:04:38.728206	APPROVED	2
558	2025	6	36	200000.00	0.00	200000.00	2025-10-25 17:04:38.728206	2025-10-25 17:04:38.728207	APPROVED	2
559	2025	7	36	150000.00	0.00	150000.00	2025-10-25 17:04:38.728208	2025-10-25 17:04:38.728208	APPROVED	2
560	2025	10	36	150000.00	0.00	150000.00	2025-10-25 17:04:38.728209	2025-10-25 17:04:38.72821	APPROVED	2
561	2025	12	36	150000.00	0.00	150000.00	2025-10-25 17:04:38.728211	2025-10-25 17:04:38.728211	APPROVED	2
565	2025	9	45	1000000.00	0.00	1000000.00	2025-10-25 17:04:38.728138	2025-10-25 17:04:38.728139	APPROVED	2
\.


--
-- Data for Name: budget_scenarios; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.budget_scenarios (id, year, scenario_name, scenario_type, department_id, global_growth_rate, inflation_rate, fx_rate, assumptions, description, is_active, created_at, created_by) FROM stdin;
1	2026	Базовый сценарий 2026	BASE	1	5.00	6.00	\N	{"headcount_growth": "6 \\u2192 7 \\u0447\\u0435\\u043b\\u043e\\u0432\\u0435\\u043a", "new_projects": 2, "cloud_migration": "partial", "server_upgrade": true}	Базовый сценарий планирования на 2026 год с умеренным ростом	t	2025-10-26 19:33:45.157758	admin
2	2026	Оптимистичный сценарий	OPTIMISTIC	1	15.00	6.00	\N	{"headcount_growth": "6 \\u2192 9 \\u0447\\u0435\\u043b\\u043e\\u0432\\u0435\\u043a", "new_projects": 4, "cloud_migration": "full", "additional_budget": "+20% \\u043d\\u0430 \\u0438\\u043d\\u0444\\u0440\\u0430\\u0441\\u0442\\u0440\\u0443\\u043a\\u0442\\u0443\\u0440\\u0443"}	Оптимистичный сценарий с активным ростом бизнеса	t	2025-10-26 19:33:45.161597	admin
3	2026	Пессимистичный сценарий	PESSIMISTIC	1	-5.00	6.00	\N	{"headcount_growth": "6 \\u2192 6 (\\u0437\\u0430\\u043c\\u043e\\u0440\\u043e\\u0437\\u043a\\u0430 \\u043d\\u0430\\u0439\\u043c\\u0430)", "new_projects": 1, "cloud_migration": "postponed", "cost_optimization": "aggressive"}	Пессимистичный сценарий с режимом экономии	t	2025-10-26 19:33:45.163455	admin
5	2026	123	BASE	2	1.00	1.00	1.0000	null	\N	t	2025-10-27 07:30:47.418383	admin
6	2026	2026	OPTIMISTIC	2	5.00	8.00	\N	null	\N	t	2025-10-27 07:33:04.864242	admin
\.


--
-- Data for Name: budget_versions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.budget_versions (id, year, version_number, version_name, department_id, scenario_id, status, created_by, created_at, submitted_at, approved_at, approved_by, comments, change_log, total_amount, total_capex, total_opex, updated_at) FROM stdin;
1	2026	1	Первоначальная версия	1	1	DRAFT	admin	2025-10-26 19:33:45.166905	\N	\N	\N	Автоматически созданная тестовая версия	\N	0.00	0.00	0.00	2025-10-26 19:33:45.166907
3	2026	1	1	2	5	DRAFT	admin	2025-10-27 07:30:57.680477	\N	\N	\N	\N	\N	0.00	0.00	0.00	2025-10-27 07:30:57.680484
6	2025	1	Базовая версия 2025	2	1	DRAFT	1	2025-10-28 20:16:48.02138	\N	\N	\N	\N	\N	0.00	0.00	0.00	2025-10-28 20:16:48.02138
4	2026	2	1	2	6	IN_REVIEW	admin	2025-10-27 08:40:06.961269	2025-10-28 21:57:48.320436	\N	\N	\N	\N	0.00	0.00	0.00	2025-10-28 21:57:48.3213
\.


--
-- Data for Name: contractors; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.contractors (id, name, short_name, inn, contact_info, is_active, created_at, updated_at, department_id) FROM stdin;
59	Бебеев Александр Владимирович	\N	\N	\N	t	2025-10-26 09:05:24.537134	2025-10-26 18:48:39.792886	2
60	Ситилинк ООО	\N	\N	\N	t	2025-10-26 09:05:24.549498	2025-10-26 18:48:39.792889	2
61	Гексагон ЦШК ООО	\N	\N	\N	t	2025-10-26 09:05:24.559761	2025-10-26 18:48:39.79289	2
62	ОБИТ ООО	\N	\N	\N	t	2025-10-26 09:05:24.579576	2025-10-26 18:48:39.79289	2
63	РОСТЕЛЕКОМ ПАО	\N	\N	\N	t	2025-10-26 09:05:24.5956	2025-10-26 18:48:39.792891	2
64	ВЫМПЕЛКОМ ПАО	\N	\N	\N	t	2025-10-26 09:05:24.602164	2025-10-26 18:48:39.792891	2
65	ВМБ-СЕРВИС АО	\N	\N	\N	t	2025-10-26 09:05:24.607628	2025-10-26 18:48:39.792892	2
66	Дядюра Андрей Васильевич	\N	\N	\N	t	2025-10-26 09:05:24.618105	2025-10-26 18:48:39.792892	2
67	Пигузов Дмитрий Валерьевич ИП	\N	\N	\N	t	2025-10-26 09:05:24.629593	2025-10-26 18:48:39.792893	2
68	Шикунова Татьяна Евгеньевна	\N	\N	\N	t	2025-10-26 09:05:24.641263	2025-10-26 18:48:39.792893	2
69	ЭВОТОР ООО	\N	\N	\N	t	2025-10-26 09:05:24.652035	2025-10-26 18:48:39.792894	2
70	ЧАТАПП ООО	\N	\N	\N	t	2025-10-26 09:05:24.657942	2025-10-26 18:48:39.792894	2
71	МТ-ТЕЛЕКОМ ООО	\N	\N	\N	t	2025-10-26 09:05:24.681553	2025-10-26 18:48:39.792894	2
72	ИНФОСТАРТ-СЕРВИС ООО	\N	\N	\N	t	2025-10-26 09:05:24.703892	2025-10-26 18:48:39.792895	2
73	Дроздов Глеб Анатольевич ИП	\N	\N	\N	t	2025-10-26 09:05:24.710697	2025-10-26 18:48:39.792895	2
74	МАНГО ТЕЛЕКОМ ООО	\N	\N	\N	t	2025-10-26 09:05:24.717493	2025-10-26 18:48:39.792896	2
75	Садыкова Евгения Олеговна	\N	\N	\N	t	2025-10-26 09:05:24.723532	2025-10-26 18:48:39.792896	2
76	Соколов Алексей Владимирович ИП	\N	\N	\N	t	2025-10-26 09:05:24.74122	2025-10-26 18:48:39.792897	2
77	Филипочкин Сергей Александрович	\N	\N	\N	t	2025-10-26 09:05:24.76418	2025-10-26 18:48:39.792897	2
78	ЛАБОРАТОРИЯ ЗАЩИТЫ ИНФОРМАЦИИ ООО	\N	\N	\N	t	2025-10-26 09:05:24.770656	2025-10-26 18:48:39.792897	2
79	КЛАСС ООО	\N	\N	\N	t	2025-10-26 09:05:24.776601	2025-10-26 18:48:39.792898	2
80	ГС1 РУС	\N	\N	\N	t	2025-10-26 09:05:24.794088	2025-10-26 18:48:39.792898	2
81	МИРАН ООО	\N	\N	\N	t	2025-10-26 09:05:24.804778	2025-10-26 18:48:39.792899	2
82	ИТ ДЖЕТ ООО	\N	\N	\N	t	2025-10-26 09:05:24.824368	2025-10-26 18:48:39.792899	2
83	МАКСИПЛЭЙС ООО	\N	\N	\N	t	2025-10-26 09:05:24.877075	2025-10-26 18:48:39.792899	2
84	ОНЛАЙН КАССА.РУ ООО	\N	\N	\N	t	2025-10-26 09:05:24.883909	2025-10-26 18:48:39.7929	2
85	ОПЕРАТОР-ЦРПТ ООО	\N	\N	\N	t	2025-10-26 09:05:24.909242	2025-10-26 18:48:39.7929	2
86	КОРЯК ЮРИЙ СЕРГЕЕВИЧ ИП	\N	\N	\N	t	2025-10-26 09:05:24.91649	2025-10-26 18:48:39.792901	2
87	ИНТЕРНЕТ РЕШЕНИЯ ООО (ОЗОН)	\N	\N	\N	t	2025-10-26 09:05:25.04836	2025-10-26 18:48:39.792901	2
88	ЖУКОВА ОЛЬГА ЛЕОНИДОВНА	\N	\N	\N	t	2025-10-26 09:05:25.073507	2025-10-26 18:48:39.792902	2
89	БЕГЕТ ООО	\N	\N	\N	t	2025-10-27 09:28:25.227249	2025-10-27 09:28:25.227252	2
90	Ватаева Сафина Сослановна	\N	\N	\N	t	2025-10-27 09:28:25.238773	2025-10-27 09:28:25.238775	2
91	ЧАСТНОЕ ЛИЦО (КАССА) - всегда ЧЕК	\N	\N	\N	t	2025-10-27 09:28:25.242318	2025-10-27 09:28:25.24232	2
\.


--
-- Data for Name: dashboard_configs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dashboard_configs (id, name, description, is_default, is_public, config, created_at, updated_at, user_id) FROM stdin;
\.


--
-- Data for Name: departments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.departments (id, name, code, description, is_active, manager_name, contact_email, contact_phone, created_at, updated_at, ftp_subdivision_name) FROM stdin;
1	del	IT	`	t				2025-10-25 15:59:37.477792	2025-10-25 20:53:36.295152	
2	IT Отдел WEST	WEST_IT		t	Шикунов Евгений	shikunov.e@w-stom.ru		2025-10-25 17:03:56.240695	2025-10-26 09:06:10.650443	(ВЕСТ) IT
\.


--
-- Data for Name: employee_kpi_goals; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.employee_kpi_goals (id, employee_id, goal_id, employee_kpi_id, year, month, target_value, actual_value, achievement_percentage, weight, status, notes, created_at, updated_at) FROM stdin;
1	1	1	\N	2025	10	\N	\N	\N	\N	ACTIVE	\N	2025-10-28 21:55:05.486198	2025-10-28 21:55:05.486202
\.


--
-- Data for Name: employee_kpis; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.employee_kpis (id, employee_id, year, month, kpi_percentage, monthly_bonus_type, quarterly_bonus_type, annual_bonus_type, monthly_bonus_base, quarterly_bonus_base, annual_bonus_base, monthly_bonus_calculated, quarterly_bonus_calculated, annual_bonus_calculated, monthly_bonus_fixed_part, quarterly_bonus_fixed_part, annual_bonus_fixed_part, department_id, notes, created_at, updated_at) FROM stdin;
1	1	2025	10	\N	PERFORMANCE_BASED	PERFORMANCE_BASED	PERFORMANCE_BASED	0.00	0.00	0.00	\N	\N	\N	\N	\N	\N	2	\N	2025-10-28 21:55:15.388592	2025-10-28 21:55:15.388599
\.


--
-- Data for Name: employees; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.employees (id, full_name, "position", employee_number, hire_date, fire_date, status, base_salary, department_id, email, phone, notes, created_at, updated_at, monthly_bonus_base, quarterly_bonus_base, annual_bonus_base) FROM stdin;
2	Волохов Александр Сергеевич	Системный администратор	\N	2025-01-01	\N	ACTIVE	100000.00	2	\N	\N	\N	2025-10-25 17:04:16.800703	2025-10-27 08:02:42.432514	15000.00	36000.00	36000.00
3	Жилев	Системный аналитик	\N	2025-09-01	\N	ACTIVE	160000.00	2	\N	\N	\N	2025-10-25 17:04:16.815051	2025-10-27 08:06:20.480481	48000.00	48000.00	48000.00
4	Свистунов Павел	Разработчик 1С	\N	2025-02-01	\N	ACTIVE	180000.00	2	\N	\N	\N	2025-10-25 17:04:16.828554	2025-10-27 08:07:47.286219	31000.00	74400.00	74400.00
6	Замятин Никита	Аналитик 1с	\N	2025-10-06	\N	ACTIVE	120000.00	2	\N	\N	\N	2025-10-25 17:04:16.855182	2025-10-27 08:08:32.126459	0.00	0.00	0.00
8	Иванов Иван Иванович	Старший разработчик	EMP-001	2025-01-15	\N	ACTIVE	0.00	2	ivanov@example.com	+7(999)123-45-67	\N	2025-10-27 07:36:34.317497	2025-10-27 08:12:24.977193	0.00	0.00	0.00
5	Шикунов Евгений	РуководительIT	\N	2025-01-01	\N	ACTIVE	300000.00	2	\N	\N	\N	2025-10-25 17:04:16.841959	2025-10-27 08:18:11.474413	200000.00	0.00	0.00
7	Колегов Никита	Аналитик данных	\N	2025-01-01	\N	ACTIVE	60000.00	2	\N	\N	\N	2025-10-25 17:04:16.867618	2025-10-27 08:24:54.617698	40000.00	96000.00	48000.00
1	Загидулин Ринат	Руководитель отдела разработки 1С	\N	2025-01-01	\N	ACTIVE	300000.00	2	\N	\N	\N	2025-10-25 17:04:16.787163	2025-10-28 14:28:25.973649	56350.00	135240.00	67620.00
\.


--
-- Data for Name: expenses; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.expenses (id, number, category_id, contractor_id, organization_id, amount, request_date, payment_date, status, is_paid, is_closed, comment, requester, created_at, updated_at, imported_from_ftp, needs_review, department_id) FROM stdin;
1	IMP-2025-04-8-0	8	\N	1	34000.00	2025-04-15 00:00:00	2025-04-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718261	2025-10-25 17:04:16.718264	f	f	2
432	0А0В-000013	45	73	2	600000.00	2025-09-25 18:00:00	2025-09-25 18:00:00	PAID	t	f	1 этап, разработка АИ приложения  помощник менеджера.  Согласовано Дмитрием Артамоновым и Масимом Смородиным	Шикунов Евгений	2025-10-26 09:16:48.393956	2025-10-27 10:51:06.681697	t	t	2
4	IMP-2025-03-10-2	10	\N	1	15000.00	2025-03-15 00:00:00	2025-03-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718268	2025-10-25 17:04:16.718269	f	f	2
5	IMP-2025-04-10-2	10	\N	1	11880.00	2025-04-15 00:00:00	2025-04-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.71827	2025-10-25 17:04:16.718271	f	f	2
6	IMP-2025-05-10-2	10	\N	1	15000.00	2025-05-15 00:00:00	2025-05-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718271	2025-10-25 17:04:16.718272	f	f	2
7	IMP-2025-06-10-2	10	\N	1	11877.00	2025-06-15 00:00:00	2025-06-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718273	2025-10-25 17:04:16.718274	f	f	2
469	ВЛ0В-000002	42	61	2	18890.00	2025-07-09 00:00:00	2025-07-09 00:00:00	PAID	t	f	Сканеры ШК для склада (еще два рабочих места)	Администратор	2025-10-26 09:38:25.396369	2025-10-26 09:38:25.39637	t	t	2
471	ВГ0В-000015	42	60	2	10603.00	2025-07-15 00:00:00	2025-07-15 00:00:00	PENDING	f	f	ситилинк. техника	Администратор	2025-10-26 09:38:25.396372	2025-10-26 09:38:25.396373	t	t	2
13	IMP-2025-02-11-3	11	\N	1	10000.00	2025-02-15 00:00:00	2025-02-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718284	2025-10-25 17:04:16.718284	f	f	2
14	IMP-2025-03-11-3	11	\N	1	10000.00	2025-03-15 00:00:00	2025-03-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718285	2025-10-25 17:04:16.718286	f	f	2
474	0В0В-002032	42	80	1	3000.00	2025-07-01 00:00:00	2025-07-01 00:00:00	PAID	t	f	\N	Шикунов Евгений	2025-10-26 09:38:25.396376	2025-10-26 09:38:25.396376	t	t	2
478	ВГ0В-000011	42	60	2	84017.00	2025-07-02 00:00:00	2025-07-02 00:00:00	PAID	t	f	ситилинк. техника	Шикунов Евгений	2025-10-26 09:38:25.396381	2025-10-26 09:38:25.396381	t	t	2
24	IMP-2025-01-12-4	12	\N	1	150000.00	2025-01-15 00:00:00	2025-01-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.7183	2025-10-25 17:04:16.718301	f	f	2
25	IMP-2025-02-12-4	12	\N	1	150000.00	2025-02-15 00:00:00	2025-02-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718302	2025-10-25 17:04:16.718302	f	f	2
26	IMP-2025-03-12-4	12	\N	1	150000.00	2025-03-15 00:00:00	2025-03-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718303	2025-10-25 17:04:16.718304	f	f	2
27	IMP-2025-04-12-4	12	\N	1	250000.00	2025-04-15 00:00:00	2025-04-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718304	2025-10-25 17:04:16.718305	f	f	2
28	IMP-2025-05-12-4	12	\N	1	250000.00	2025-05-15 00:00:00	2025-05-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718306	2025-10-25 17:04:16.718306	f	f	2
29	IMP-2025-06-12-4	12	\N	1	200000.00	2025-06-15 00:00:00	2025-06-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718307	2025-10-25 17:04:16.718308	f	f	2
479	ВГ0В-000012	42	82	2	21000.00	2025-07-02 00:00:00	2025-07-02 00:00:00	PAID	t	f	аутсорс краснодар	Шикунов Евгений	2025-10-26 09:38:25.396382	2025-10-26 09:38:25.396383	t	t	2
480	0В0В-002552	41	74	1	50000.00	2025-07-23 00:00:00	2025-07-23 00:00:00	PAID	t	f	Организация должна стоять Вест, не могу выбрать расчетный счет Веста - Тбанк	Шикунов Евгений	2025-10-26 09:38:25.396383	2025-10-26 09:38:25.396384	t	t	2
481	ВС0В-000575	42	79	2	43590.00	2025-07-25 00:00:00	2025-07-25 00:00:00	PAID	t	f	\N	Шикунов Евгений	2025-10-26 09:38:25.396384	2025-10-26 09:38:25.396385	t	t	2
482	СВ0В-000008	42	79	2	48590.00	2025-07-25 00:00:00	2025-07-25 00:00:00	PAID	t	f	\N	Шикунов Евгений	2025-10-26 09:38:25.396386	2025-10-26 09:38:25.396386	t	t	2
483	ВД0В-000023	42	79	2	43590.00	2025-07-25 00:00:00	2025-07-25 00:00:00	PAID	t	f	\N	Шикунов Евгений	2025-10-26 09:38:25.396387	2025-10-26 09:38:25.396387	t	t	2
484	ЛП0В-000017	42	79	2	43590.00	2025-07-25 00:00:00	2025-07-25 00:00:00	PAID	t	f	\N	Шикунов Евгений	2025-10-26 09:38:25.396388	2025-10-26 09:38:25.396389	t	t	2
487	ВГ0В-000025	15	67	2	135000.00	2025-08-06 00:00:00	2025-08-06 00:00:00	PAID	t	f	Доработка 1с.	Шикунов Евгений	2025-10-26 09:38:25.396392	2025-10-26 09:38:25.396392	t	t	2
470	ВГ0В-000014	20	59	2	23000.00	2025-07-14 21:00:00	2025-07-14 21:00:00	PENDING	f	f	Обслуживвание орг техники	Администратор	2025-10-26 09:38:25.396371	2025-10-26 09:52:07.850519	t	t	2
486	ВГ0В-000023	19	59	2	44000.00	2025-07-31 21:00:00	2025-07-31 21:00:00	PAID	t	f	Обслуживвание орг техники	Шикунов Евгений	2025-10-26 09:38:25.39639	2025-10-26 09:52:36.818645	t	t	2
473	ВГ0В-000007	16	77	2	40000.00	2025-06-26 21:00:00	2025-06-26 21:00:00	PAID	t	f	\N	Шикунов Евгений	2025-10-26 09:38:25.396375	2025-10-26 10:07:49.466562	t	t	2
472	ВГ0В-000005	19	59	2	7400.00	2025-06-26 21:00:00	2025-06-26 21:00:00	PAID	t	f	Обслуживвание орг техники	Шикунов Евгений	2025-10-26 09:38:25.396373	2025-10-26 10:11:48.324278	t	t	2
12	IMP-2025-01-11-3	11	66	1	10000.00	2025-01-14 21:00:00	2025-01-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718282	2025-10-26 10:12:11.491323	f	f	2
475	ВГ0В-000009	14	78	2	105000.00	2025-06-30 21:00:00	2025-06-30 21:00:00	PAID	t	f	\N	Шикунов Евгений	2025-10-26 09:38:25.396377	2025-10-26 10:15:34.731483	t	t	2
477	ВГ0В-000010	24	81	2	40000.00	2025-07-01 21:00:00	2025-07-01 21:00:00	PAID	t	f	Оплата колокейшена серверов 1с.	Шикунов Евгений	2025-10-26 09:38:25.396379	2025-10-26 10:17:08.144925	t	t	2
476	ВА0В-000001	24	81	2	40000.00	2025-07-01 18:00:00	2025-07-01 18:00:00	PAID	t	f	На колокейшн серверов	Шикунов Евгений	2025-10-26 09:38:25.396378	2025-10-26 10:17:26.44407	t	t	2
37	IMP-2025-02-13-5	13	75	1	25000.00	2025-02-14 21:00:00	2025-02-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718319	2025-10-26 10:19:00.674032	f	f	2
17	IMP-2025-06-11-3	11	66	1	10000.00	2025-06-14 21:00:00	2025-06-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.71829	2025-10-26 10:33:17.343488	f	f	2
2	IMP-2025-05-9-1	9	78	1	119988.00	2025-05-14 21:00:00	2025-05-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718265	2025-10-26 10:34:16.382472	f	f	2
16	IMP-2025-05-11-3	11	66	1	10000.00	2025-05-14 21:00:00	2025-05-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718289	2025-10-26 10:35:46.447604	f	f	2
15	IMP-2025-04-11-3	11	66	1	10000.00	2025-04-14 21:00:00	2025-04-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718287	2025-10-26 10:36:56.264644	f	f	2
485	ВГ0В-000022	26	60	2	196585.00	2025-07-24 21:00:00	2025-07-24 21:00:00	PAID	t	f	ситилинк. техника	Шикунов Евгений	2025-10-26 09:38:25.396389	2025-10-27 10:31:20.063419	t	t	2
38	IMP-2025-03-13-5	13	\N	1	25000.00	2025-03-15 00:00:00	2025-03-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.71832	2025-10-25 17:04:16.718321	f	f	2
491	0В0В-002849	15	84	1	4950.00	2025-08-13 00:00:00	2025-08-13 00:00:00	PAID	t	f	Обучение и консультарции по Честному знаку\nНе могу установить банковский счет, принадлежащий Вест.	Шикунов Евгений	2025-10-26 09:38:25.396396	2025-10-26 09:38:25.396397	t	t	2
496	0В0В-002994	42	85	1	30000.00	2025-08-18 00:00:00	2025-08-18 00:00:00	PAID	t	f	Для честного знака	Шикунов Евгений	2025-10-26 09:38:25.396403	2025-10-26 09:38:25.396403	t	t	2
497	ВГ0В-000035	42	86	2	15000.00	2025-08-18 00:00:00	2025-08-18 00:00:00	PAID	t	f	Обслуживание техники в Краснодаре	Шикунов Евгений	2025-10-26 09:38:25.396404	2025-10-26 09:38:25.396404	t	t	2
498	ВГ0В-000042	42	60	2	89587.00	2025-08-21 00:00:00	2025-08-21 00:00:00	PAID	t	f	ситилинк. техника	Шикунов Евгений	2025-10-26 09:38:25.396405	2025-10-26 09:38:25.396406	t	t	2
501	0В0В-003193	41	74	1	45000.00	2025-08-28 00:00:00	2025-08-28 00:00:00	PAID	t	f	Организация должна стоять Вест,	Шикунов Евгений	2025-10-26 09:38:25.396409	2025-10-26 09:38:25.396409	t	t	2
60	IMP-2025-03-16-8	16	\N	1	40000.00	2025-03-15 00:00:00	2025-03-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718352	2025-10-25 17:04:16.718352	f	f	2
61	IMP-2025-04-16-8	16	\N	1	18500.00	2025-04-15 00:00:00	2025-04-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718353	2025-10-25 17:04:16.718354	f	f	2
71	IMP-2025-06-17-9	17	68	1	150000.00	2025-06-14 21:00:00	2025-06-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718367	2025-10-26 09:47:45.140848	f	f	2
70	IMP-2025-05-17-9	17	68	1	200000.00	2025-05-14 21:00:00	2025-05-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718366	2025-10-26 09:47:53.500233	f	f	2
69	IMP-2025-04-17-9	17	68	1	150000.00	2025-04-14 21:00:00	2025-04-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718364	2025-10-26 09:47:59.849504	f	f	2
499	ВГ0В-000047	17	68	2	160000.00	2025-08-21 21:00:00	2025-08-21 21:00:00	PAID	t	f	Разработка приложения визитной активности	Шикунов Евгений	2025-10-26 09:38:25.396406	2025-10-26 09:48:10.684066	t	t	2
489	ВГ0В-000027	13	75	2	50000.00	2025-08-05 21:00:00	2025-08-05 21:00:00	PAID	t	f	РАботник по битриксу	Шикунов Евгений	2025-10-26 09:38:25.396394	2025-10-26 09:50:09.48798	t	t	2
500	ВГ0В-000059	24	81	2	40000.00	2025-08-27 21:00:00	2025-08-27 21:00:00	PAID	t	f	Оплата колокейшена серверов 1с.	Шикунов Евгений	2025-10-26 09:38:25.396408	2025-10-26 09:51:26.910221	t	t	2
490	ВГ0В-000028	23	83	2	78800.00	2025-08-11 21:00:00	2025-08-11 21:00:00	PAID	t	f	доплата на сервреное оборудование Битрикс24\nБИК банка неверный	Шикунов Евгений	2025-10-26 09:38:25.396395	2025-10-26 09:51:42.410736	t	t	2
74	IMP-2025-01-18-10	18	\N	1	60000.00	2025-01-15 00:00:00	2025-01-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718371	2025-10-25 17:04:16.718372	f	f	2
504	ВГ0В-000018	22	88	2	58300.00	2025-07-20 21:00:00	2025-07-20 21:00:00	PAID	t	f	Настройка и установка сервера	Шикунов Евгений	2025-10-26 09:38:25.396412	2025-10-26 09:52:19.475178	t	t	2
51	IMP-2025-06-14-6	14	78	2	200000.00	2025-06-14 21:00:00	2025-06-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718339	2025-10-26 09:36:21.216729	f	f	2
50	IMP-2025-05-14-6	14	78	2	147000.00	2025-05-14 21:00:00	2025-05-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718337	2025-10-26 09:36:32.935344	f	f	2
49	IMP-2025-04-14-6	14	78	1	199500.00	2025-04-14 21:00:00	2025-04-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718336	2025-10-26 09:36:42.587982	f	f	2
48	IMP-2025-03-14-6	14	78	2	100000.00	2025-03-14 21:00:00	2025-03-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718334	2025-10-26 09:36:53.255364	f	f	2
488	ВГ0В-000026	15	67	2	250000.00	2025-08-05 21:00:00	2025-08-05 21:00:00	PAID	t	f	Настройки склада	Шикунов Евгений	2025-10-26 09:38:25.396393	2025-10-26 10:05:29.663603	t	t	2
494	ВГ0В-000031	16	77	2	40000.00	2025-08-12 21:00:00	2025-08-12 21:00:00	PAID	t	f	Аналитик даных	Шикунов Евгений	2025-10-26 09:38:25.3964	2025-10-26 10:06:27.983886	t	t	2
502	ВГ0В-000016	16	77	2	40000.00	2025-07-20 21:00:00	2025-07-20 21:00:00	PAID	t	f	Аналитик даных	Шикунов Евгений	2025-10-26 09:38:25.39641	2025-10-26 10:07:42.107662	t	t	2
493	ВГ0В-000030	9	78	2	32720.00	2025-08-12 21:00:00	2025-08-12 21:00:00	PAID	t	f	Лицензия на сайт Учебного центра.	Шикунов Евгений	2025-10-26 09:38:25.396399	2025-10-26 10:15:42.962629	t	t	2
492	ВГ0В-000029	14	78	2	199500.00	2025-08-12 21:00:00	2025-08-12 21:00:00	PAID	t	f	Битрриикс 24 работы.	Шикунов Евгений	2025-10-26 09:38:25.396398	2025-10-26 10:16:01.361806	t	t	2
503	ВГ0В-000017	14	78	2	28000.00	2025-07-20 21:00:00	2025-07-20 21:00:00	PAID	t	f	Битрриикс 24 работы.	Шикунов Евгений	2025-10-26 09:38:25.396411	2025-10-26 10:16:15.939601	t	t	2
41	IMP-2025-06-13-5	13	75	1	25000.00	2025-06-14 21:00:00	2025-06-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718324	2025-10-26 10:18:42.15077	f	f	2
40	IMP-2025-05-13-5	13	75	1	25000.00	2025-05-14 21:00:00	2025-05-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718323	2025-10-26 10:18:48.226465	f	f	2
39	IMP-2025-04-13-5	13	75	1	25000.00	2025-04-14 21:00:00	2025-04-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718322	2025-10-26 10:18:54.696735	f	f	2
57	IMP-2025-05-15-7	15	82	1	39100.00	2025-05-14 21:00:00	2025-05-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718347	2025-10-26 10:34:50.845145	f	f	2
62	IMP-2025-05-16-8	16	77	1	40000.00	2025-05-14 21:00:00	2025-05-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718354	2025-10-26 10:34:59.250689	f	f	2
56	IMP-2025-04-15-7	15	76	1	100000.00	2025-04-14 21:00:00	2025-04-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718346	2025-10-26 10:36:41.692223	f	f	2
495	ВГ0В-000032	23	83	2	10000.00	2025-08-14 21:00:00	2025-08-14 21:00:00	PAID	t	f	\N	Шикунов Евгений	2025-10-26 09:38:25.396401	2025-10-27 10:16:07.430944	t	t	2
75	IMP-2025-02-18-10	18	\N	1	60000.00	2025-02-15 00:00:00	2025-02-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718373	2025-10-25 17:04:16.718373	f	f	2
76	IMP-2025-03-18-10	18	\N	1	60000.00	2025-03-15 00:00:00	2025-03-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718374	2025-10-25 17:04:16.718375	f	f	2
77	IMP-2025-04-18-10	18	\N	1	65600.00	2025-04-15 00:00:00	2025-04-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718376	2025-10-25 17:04:16.718376	f	f	2
468	ВГ0В-000019	19	59	2	39900.00	2025-07-21 18:00:00	2025-07-21 18:00:00	PENDING	f	f	Обслуживвание орг техники	Администратор	2025-10-26 09:38:25.396366	2025-10-26 10:11:38.939063	t	t	2
97	IMP-2025-06-20-12	20	59	1	17000.00	2025-06-14 21:00:00	2025-06-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718404	2025-10-26 10:33:25.361158	f	f	2
106	IMP-2025-06-21-13	21	59	1	12650.00	2025-06-14 21:00:00	2025-06-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718417	2025-10-26 10:33:39.131188	f	f	2
88	IMP-2025-05-19-11	19	59	1	15000.00	2025-05-14 21:00:00	2025-05-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718391	2025-10-26 10:34:24.320558	f	f	2
96	IMP-2025-05-20-12	20	59	1	11800.00	2025-05-14 21:00:00	2025-05-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718402	2025-10-26 10:35:08.546693	f	f	2
85	IMP-2025-02-19-11	19	\N	1	15000.00	2025-02-15 00:00:00	2025-02-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718387	2025-10-25 17:04:16.718387	f	f	2
86	IMP-2025-03-19-11	19	\N	1	15000.00	2025-03-15 00:00:00	2025-03-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718388	2025-10-25 17:04:16.718389	f	f	2
87	IMP-2025-04-19-11	19	\N	1	15000.00	2025-04-15 00:00:00	2025-04-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.71839	2025-10-25 17:04:16.71839	f	f	2
78	IMP-2025-05-18-10	18	59	1	60000.00	2025-05-14 21:00:00	2025-05-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718377	2025-10-26 10:35:18.00767	f	f	2
105	IMP-2025-05-21-13	21	59	1	30000.00	2025-05-14 21:00:00	2025-05-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718415	2025-10-26 10:35:24.651802	f	f	2
104	IMP-2025-04-21-13	21	59	1	21000.00	2025-04-14 21:00:00	2025-04-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718414	2025-10-26 10:36:30.837265	f	f	2
95	IMP-2025-04-20-12	20	59	1	20000.00	2025-04-14 21:00:00	2025-04-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718401	2025-10-26 10:37:09.640226	f	f	2
93	IMP-2025-02-20-12	20	\N	1	20000.00	2025-02-15 00:00:00	2025-02-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718398	2025-10-25 17:04:16.718398	f	f	2
94	IMP-2025-03-20-12	20	\N	1	20000.00	2025-03-15 00:00:00	2025-03-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718399	2025-10-25 17:04:16.7184	f	f	2
101	IMP-2025-01-21-13	21	\N	1	30000.00	2025-01-15 00:00:00	2025-01-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718409	2025-10-25 17:04:16.71841	f	f	2
102	IMP-2025-02-21-13	21	\N	1	30000.00	2025-02-15 00:00:00	2025-02-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718411	2025-10-25 17:04:16.718411	f	f	2
103	IMP-2025-03-21-13	21	\N	1	30000.00	2025-03-15 00:00:00	2025-03-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718412	2025-10-25 17:04:16.718413	f	f	2
505	0А0В-000037	45	73	4	400000.00	2025-11-02 15:00:00	2025-11-02 15:00:00	PENDING	f	f	2 этап, разработка АИ приложения  помощник менеджера.  Согласовано Дмитрием Артамоновым и Масимом Смородиным\nАкт прилагаю	Шикунов Евгений	2025-10-27 08:55:41.31332	2025-10-27 08:57:47.013661	t	t	2
513	4564	12	\N	1	200000.00	2025-07-23 21:00:00	\N	PAID	t	f	\N	\N	2025-10-27 09:33:22.14784	2025-10-27 09:33:22.147846	f	f	2
111	IMP-2025-05-22-14	22	\N	1	150000.00	2025-05-15 00:00:00	2025-05-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718424	2025-10-25 17:04:16.718424	f	f	2
36	IMP-2025-01-13-5	13	75	1	25000.00	2025-01-14 21:00:00	2025-01-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718317	2025-10-26 10:19:05.81986	f	f	2
112	IMP-2025-06-22-14	22	88	1	715674.00	2025-06-14 21:00:00	2025-06-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718425	2025-10-26 10:33:51.545627	f	f	2
130	IMP-2025-06-26-18	26	60	1	88870.00	2025-06-14 21:00:00	2025-06-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.71845	2025-10-26 10:33:58.925395	f	f	2
117	IMP-2025-03-24-16	24	\N	1	50000.00	2025-03-15 00:00:00	2025-03-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718432	2025-10-25 17:04:16.718433	f	f	2
140	IMP-2025-06-27-19	27	60	1	36980.00	2025-06-14 21:00:00	2025-06-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718465	2025-10-26 10:34:05.629084	f	f	2
129	IMP-2025-05-26-18	26	60	1	92210.00	2025-05-14 21:00:00	2025-05-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718449	2025-10-26 10:34:31.016878	f	f	2
139	IMP-2025-05-27-19	27	60	1	7742.00	2025-05-14 21:00:00	2025-05-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718463	2025-10-26 10:34:38.728295	f	f	2
113	IMP-2025-05-23-15	23	83	1	4881.00	2025-05-14 21:00:00	2025-05-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718427	2025-10-26 10:35:35.092933	f	f	2
506	ВЛ0В-000189	42	61	2	9260.00	2025-10-27 00:00:00	2025-10-27 00:00:00	PENDING	f	f	Оплата за сканеры на склад	Шикунов Евгений	2025-10-27 09:28:25.23048	2025-10-27 09:28:25.230483	t	t	2
507	0В0В-004037	41	69	1	2700.00	2025-10-27 00:00:00	2025-10-27 00:00:00	PENDING	f	f	Оплата ПО кассы Выставка	Шикунов Евгений	2025-10-27 09:28:25.230484	2025-10-27 09:28:25.230485	t	t	2
124	IMP-2025-02-25-17	25	\N	1	200000.00	2025-02-15 00:00:00	2025-02-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718442	2025-10-25 17:04:16.718443	f	f	2
125	IMP-2025-04-25-17	25	\N	1	135180.00	2025-04-15 00:00:00	2025-04-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718443	2025-10-25 17:04:16.718444	f	f	2
508	ВГ0В-000006	42	59	2	1000.00	2025-06-27 00:00:00	2025-06-27 00:00:00	PENDING	f	f	тест	Шикунов Евгений	2025-10-27 09:28:25.230485	2025-10-27 09:28:25.230486	t	t	2
128	IMP-2025-04-26-18	26	\N	1	89680.00	2025-04-15 00:00:00	2025-04-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718448	2025-10-25 17:04:16.718448	f	f	2
510	0В0В-003026	12	89	1	49190.00	2025-08-20 00:00:00	2025-08-20 00:00:00	PAID	t	f	подписки на сервера	Шикунов Евгений	2025-10-27 09:28:25.239211	2025-10-27 09:28:25.239213	t	t	2
511	0В0В-003132	\N	90	1	7389.00	2025-08-25 00:00:00	2025-08-25 00:00:00	PAID	t	f	\N	Шикунов Евгений	2025-10-27 09:28:25.242744	2025-10-27 09:28:25.242745	t	t	2
512	0В0В-003133	\N	91	1	2537.00	2025-08-25 00:00:00	2025-08-25 00:00:00	PAID	t	f	\N	Шикунов Евгений	2025-10-27 09:28:25.305269	2025-10-27 09:28:25.305272	t	t	2
509	ВГ0В-000021	17	68	2	115000.00	2025-07-24 21:00:00	2025-07-24 21:00:00	PAID	t	f	Разработка приложения визитной активности	Шикунов Евгений	2025-10-27 09:28:25.230487	2025-10-27 09:29:57.738772	t	t	2
137	IMP-2025-02-27-19	27	\N	1	100000.00	2025-02-15 00:00:00	2025-02-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718461	2025-10-25 17:04:16.718461	f	f	2
138	IMP-2025-03-27-19	27	\N	1	180000.00	2025-03-15 00:00:00	2025-03-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718462	2025-10-25 17:04:16.718463	f	f	2
142	IMP-2025-01-28-20	28	\N	1	20000.00	2025-01-15 00:00:00	2025-01-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718468	2025-10-25 17:04:16.718468	f	f	2
143	IMP-2025-02-28-20	28	\N	1	20000.00	2025-02-15 00:00:00	2025-02-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718469	2025-10-25 17:04:16.71847	f	f	2
144	IMP-2025-03-28-20	28	\N	1	20000.00	2025-03-15 00:00:00	2025-03-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.71847	2025-10-25 17:04:16.718471	f	f	2
145	IMP-2025-01-29-21	29	\N	1	200000.00	2025-01-15 00:00:00	2025-01-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718472	2025-10-25 17:04:16.718472	f	f	2
146	IMP-2025-06-29-21	29	\N	1	45820.00	2025-06-15 00:00:00	2025-06-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718473	2025-10-25 17:04:16.718474	f	f	2
147	IMP-2025-01-30-22	30	\N	1	70000.00	2025-01-15 00:00:00	2025-01-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718475	2025-10-25 17:04:16.718475	f	f	2
148	IMP-2025-02-30-22	30	\N	1	70000.00	2025-02-15 00:00:00	2025-02-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718476	2025-10-25 17:04:16.718477	f	f	2
149	IMP-2025-01-31-23	31	\N	1	70000.00	2025-01-15 00:00:00	2025-01-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718477	2025-10-25 17:04:16.718478	f	f	2
150	IMP-2025-01-32-24	32	\N	1	20000.00	2025-01-15 00:00:00	2025-01-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718479	2025-10-25 17:04:16.718479	f	f	2
151	IMP-2025-02-32-24	32	\N	1	170000.00	2025-02-15 00:00:00	2025-02-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.71848	2025-10-25 17:04:16.718481	f	f	2
152	IMP-2025-03-32-24	32	\N	1	120000.00	2025-03-15 00:00:00	2025-03-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718482	2025-10-25 17:04:16.718482	f	f	2
159	IMP-2025-04-34-26	34	60	1	110000.00	2025-04-14 21:00:00	2025-04-19 21:00:00	PAID	t	f	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718492	2025-10-26 10:36:14.873199	f	f	2
156	IMP-2025-01-33-25	33	\N	1	80000.00	2025-01-15 00:00:00	2025-01-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718487	2025-10-25 17:04:16.718488	f	f	2
157	IMP-2025-01-34-26	34	\N	1	70000.00	2025-01-15 00:00:00	2025-01-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718489	2025-10-25 17:04:16.718489	f	f	2
158	IMP-2025-03-34-26	34	\N	1	70000.00	2025-03-15 00:00:00	2025-03-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.71849	2025-10-25 17:04:16.718491	f	f	2
162	IMP-2025-01-35-27	35	\N	1	110000.00	2025-01-15 00:00:00	2025-01-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718496	2025-10-25 17:04:16.718497	f	f	2
163	IMP-2025-02-35-27	35	\N	1	290000.00	2025-02-15 00:00:00	2025-02-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718497	2025-10-25 17:04:16.718498	f	f	2
164	IMP-2025-03-36-28	36	\N	1	90000.00	2025-03-15 00:00:00	2025-03-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718499	2025-10-25 17:04:16.718499	f	f	2
165	IMP-2025-04-36-28	36	\N	1	209990.00	2025-04-15 00:00:00	2025-04-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.7185	2025-10-25 17:04:16.718501	f	f	2
166	IMP-2025-05-36-28	36	\N	1	326000.00	2025-05-15 00:00:00	2025-05-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718502	2025-10-25 17:04:16.718502	f	f	2
167	IMP-2025-06-36-28	36	\N	1	136820.00	2025-06-15 00:00:00	2025-06-20 00:00:00	PAID	t	t	Импортировано из файла Планфакт2025.xlsx (лист 'факт')	\N	2025-10-25 17:04:16.718503	2025-10-25 17:04:16.718504	f	f	2
408	ВГ0В-000127	42	60	2	6995.00	2025-09-19 00:00:00	2025-09-19 00:00:00	PAID	t	f	ситилинк. техника	Администратор	2025-10-26 09:16:48.393917	2025-10-26 09:16:48.393922	t	t	2
409	ВЛ0В-000129	12	62	2	38304.00	2025-10-14 00:00:00	2025-10-14 00:00:00	PAID	t	f	№ договора Д166861 от 26.12.2024г. Интернет Салова 46\n Счет должен быть оплачен до 20.10.2025. \n\nЗаявка проверена 	Лебедев Павел	2025-10-26 09:16:48.393923	2025-10-26 09:16:48.393924	t	t	2
410	ВГ0В-000195	20	59	2	28100.00	2025-10-13 00:00:00	2025-10-13 00:00:00	PAID	t	f	Обслуживвание орг техники\\заправка картриджей	Шикунов Евгений	2025-10-26 09:16:48.393925	2025-10-26 09:16:48.393925	t	t	2
412	0В0В-003808	12	64	1	10696.07	2025-10-13 00:00:00	2025-10-13 00:00:00	PAID	t	f	Мобильная связь	Шикунов Евгений	2025-10-26 09:16:48.393928	2025-10-26 09:16:48.393928	t	t	2
413	0В0В-003811	12	65	1	3511.20	2025-10-14 00:00:00	2025-10-14 00:00:00	PAID	t	f	Интернет	Шикунов Евгений	2025-10-26 09:16:48.393929	2025-10-26 09:16:48.39393	t	t	2
414	0В0В-003812	12	65	1	38367.00	2025-10-14 00:00:00	2025-10-14 00:00:00	PAID	t	f	Интернет основной офис	Шикунов Евгений	2025-10-26 09:16:48.393931	2025-10-26 09:16:48.393931	t	t	2
447	ВГ0В-000067	14	78	2	147000.00	2025-08-31 21:00:00	2025-08-31 15:00:00	PAID	t	f	доработки и обслуживание Бирикс 24	Шикунов Евгений	2025-10-26 09:16:48.393978	2025-10-27 10:55:04.08362	t	t	2
418	ВЛ0В-000137	12	64	2	18083.30	2025-10-14 00:00:00	2025-10-14 00:00:00	PAID	t	f	Оплата телефонии договор 891588088	Шикунов Евгений	2025-10-26 09:16:48.393936	2025-10-26 09:16:48.393937	t	t	2
429	0М0В-000009	12	64	2	2985.35	2025-10-22 21:00:00	2025-10-22 21:00:00	PAID	t	f	Услуги связи	Шикунов Евгений	2025-10-26 09:16:48.393952	2025-10-26 09:40:41.953174	t	t	2
421	ВГ0В-000221	41	69	2	200.00	2025-10-16 00:00:00	2025-10-16 00:00:00	PAID	t	f	Оплата ПО кассы	Шикунов Евгений	2025-10-26 09:16:48.39394	2025-10-26 09:16:48.393941	t	t	2
422	ВГ0В-000224	10	70	2	4000.00	2025-10-16 00:00:00	2025-10-16 00:00:00	PAID	t	f	Интеграция ватсап и битркис24	Шикунов Евгений	2025-10-26 09:16:48.393942	2025-10-26 09:16:48.393943	t	t	2
423	0В0В-003959	41	69	1	133.34	2025-10-20 00:00:00	2025-10-20 00:00:00	PAID	t	f	Оплата ПО кассы	Шикунов Евгений	2025-10-26 09:16:48.393943	2025-10-26 09:16:48.393944	t	t	2
424	0В0В-003960	41	69	1	6500.00	2025-10-20 00:00:00	2025-10-20 00:00:00	PAID	t	f	Оплата ПО кассы 	Шикунов Евгений	2025-10-26 09:16:48.393945	2025-10-26 09:16:48.393945	t	t	2
425	0В0В-003961	41	69	1	1800.00	2025-10-20 00:00:00	2025-10-20 00:00:00	PAID	t	f	Оплата ПО кассы	Шикунов Евгений	2025-10-26 09:16:48.393946	2025-10-26 09:16:48.393947	t	t	2
427	0В0В-003978	12	71	1	1100.00	2025-10-22 00:00:00	2025-10-22 00:00:00	PAID	t	f	Интернет на Уткина	Шикунов Евгений	2025-10-26 09:16:48.393949	2025-10-26 09:16:48.39395	t	t	2
428	0А0В-000035	12	64	2	34584.72	2025-10-22 21:00:00	2025-10-22 21:00:00	PAID	t	f	Услуги связи	Шикунов Евгений	2025-10-26 09:16:48.39395	2025-10-26 09:40:53.686933	t	t	2
431	ВГ0В-000248	41	72	2	1850.00	2025-10-23 00:00:00	2025-10-23 00:00:00	PAID	t	f	Модуль для бухгалетрии	Шикунов Евгений	2025-10-26 09:16:48.393955	2025-10-26 09:16:48.393955	t	t	2
420	ВС0В-000874	12	64	2	1062.59	2025-10-12 21:00:00	2025-10-12 21:00:00	PAID	t	f	Услуги связи	Шикунов Евгений	2025-10-26 09:16:48.393939	2025-10-26 09:41:06.667693	t	t	2
416	0В0В-003814	11	66	1	8000.00	2025-10-13 21:00:00	2025-10-13 21:00:00	PAID	t	f	Почтовый сервер.	Шикунов Евгений	2025-10-26 09:16:48.393933	2025-10-26 09:42:21.869861	t	t	2
435	ВГ0В-000161	41	72	2	2150.00	2025-09-29 00:00:00	2025-09-29 00:00:00	PAID	t	f	Модуль для бухгалетрии	Шикунов Евгений	2025-10-26 09:16:48.393961	2025-10-26 09:16:48.393961	t	t	2
437	ВГ0В-000165	15	76	2	20000.00	2025-10-01 00:00:00	2025-10-01 00:00:00	PAID	t	f	1с доработки по зонам доставки в заказах покупателей.	Шикунов Евгений	2025-10-26 09:16:48.393964	2025-10-26 09:16:48.393964	t	t	2
441	ВГ0В-000172	42	60	2	55990.00	2025-10-02 00:00:00	2025-10-02 00:00:00	PAID	t	f	ситилинк. техника, ноутбук	Шикунов Евгений	2025-10-26 09:16:48.393969	2025-10-26 09:16:48.39397	t	t	2
443	ВГ0В-000174	14	78	2	199500.00	2025-10-07 00:00:00	2025-10-07 00:00:00	PAID	t	f	Дополнительные услуги по настройке портала Битрикс24	Шикунов Евгений	2025-10-26 09:16:48.393972	2025-10-26 09:16:48.393973	t	t	2
444	0В0В-003744	42	79	1	61200.00	2025-10-14 00:00:00	2025-10-14 00:00:00	PAID	t	f	Торговый экваринг, в планах его небыло.\n\nЗаявка проверена	Шикунов Евгений	2025-10-26 09:16:48.393973	2025-10-26 09:16:48.393974	t	t	2
445	ВГ0В-000186	10	70	2	4000.00	2025-10-06 00:00:00	2025-10-06 00:00:00	PAID	t	f	Интеграция ватсап и битркис24	Шикунов Евгений	2025-10-26 09:16:48.393975	2025-10-26 09:16:48.393975	t	t	2
449	ВГ0В-000074	42	60	2	65090.00	2025-09-02 00:00:00	2025-09-02 00:00:00	PAID	t	f	ситилинк. техника, Ноутбук для Фин директора	Шикунов Евгений	2025-10-26 09:16:48.39398	2025-10-26 09:16:48.393981	t	t	2
450	ВГ0В-000080	14	78	2	59500.00	2025-09-04 00:00:00	2025-09-04 00:00:00	PAID	t	f	Дополнительные услуги по настройке портала\n1C-Битрикс24 портала	Шикунов Евгений	2025-10-26 09:16:48.393982	2025-10-26 09:16:48.393982	t	t	2
434	ВГ0В-000137	13	75	2	50000.00	2025-09-22 21:00:00	2025-09-22 21:00:00	PAID	t	f	внештатный работник по битриксу	Шикунов Евгений	2025-10-26 09:16:48.393959	2025-10-26 09:35:49.591744	t	t	2
415	0В0В-003813	11	66	1	8000.00	2025-10-13 21:00:00	2025-10-13 21:00:00	PAID	t	f	Почтовый сервер	Шикунов Евгений	2025-10-26 09:16:48.393932	2025-10-26 09:42:31.799817	t	t	2
436	0В0В-003700	12	74	1	45000.00	2025-09-30 21:00:00	2025-09-30 21:00:00	PAID	t	f	Связь телефония, предоплата	Шикунов Евгений	2025-10-26 09:16:48.393962	2025-10-26 09:50:58.766564	t	t	2
433	0В0В-003604	12	74	1	30741.00	2025-09-21 21:00:00	2025-09-21 21:00:00	PAID	t	f	Оборудование, телефоны.	Шикунов Евгений	2025-10-26 09:16:48.393958	2025-10-26 09:51:06.783844	t	t	2
417	ВГ0В-000198	15	67	2	45000.00	2025-10-13 21:00:00	2025-10-13 21:00:00	PAID	t	f	Настройки склада.	Шикунов Евгений	2025-10-26 09:16:48.393935	2025-10-26 10:05:17.994232	t	t	2
446	ВГ0В-000066	15	67	2	246000.00	2025-09-01 21:00:00	2025-09-01 21:00:00	PAID	t	f	Настройки склада.\nсогл Артамонов	Шикунов Евгений	2025-10-26 09:16:48.393976	2025-10-26 10:05:23.895159	t	t	2
411	ВГ0В-000196	12	63	2	19600.00	2025-10-08 21:00:00	2025-10-08 21:00:00	PAID	t	f	оплата интернета офис спб	Шикунов Евгений	2025-10-26 09:16:48.393926	2025-10-26 10:05:54.886893	t	t	2
442	ВГ0В-000173	16	77	2	40000.00	2025-10-01 21:00:00	2025-10-01 21:00:00	PAID	t	f	Аналитик данных	Шикунов Евгений	2025-10-26 09:16:48.393971	2025-10-26 10:06:13.529462	t	t	2
439	ВГ0В-000170	19	59	2	6600.00	2025-10-01 21:00:00	2025-10-01 21:00:00	PAID	t	f	Обслуживвание орг техники	Шикунов Евгений	2025-10-26 09:16:48.393966	2025-10-26 10:11:18.513266	t	t	2
438	ВГ0В-000169	19	59	2	33000.00	2025-09-30 21:00:00	2025-09-30 21:00:00	PAID	t	f	Обслуживвание орг техники	Шикунов Евгений	2025-10-26 09:16:48.393965	2025-10-26 10:11:26.321524	t	t	2
448	ВГ0В-000068	9	78	2	104700.00	2025-08-31 21:00:00	2025-08-31 21:00:00	PAID	t	f	Лицензия Бирикс 24	Шикунов Евгений	2025-10-26 09:16:48.393979	2025-10-26 10:16:28.975141	t	t	2
426	0А0В-000033	36	64	2	51240.00	2025-10-21 21:00:00	2025-10-21 21:00:00	PAID	t	f	Услуги связи виртаульная АТС, для записей звонов с мобильных и интеграция с Битрикс24	Шикунов Евгений	2025-10-26 09:16:48.393948	2025-10-27 06:22:45.627327	t	t	2
440	ВГ0В-000171	25	60	2	281176.00	2025-10-01 21:00:00	2025-10-01 21:00:00	PAID	t	f	ситилинк. техника, компьютеы и мониторы	Шикунов Евгений	2025-10-26 09:16:48.393968	2025-10-27 10:32:45.062949	t	t	2
451	ВГ0В-000081	42	82	2	66000.00	2025-09-04 00:00:00	2025-09-04 00:00:00	PAID	t	f	1с модуль План\\факт	Шикунов Евгений	2025-10-26 09:16:48.393983	2025-10-26 09:16:48.393984	t	t	2
452	ВГ0В-000084	10	70	2	4000.00	2025-09-04 00:00:00	2025-09-04 00:00:00	PAID	t	f	Интеграция ватсап и битркис24	Шикунов Евгений	2025-10-26 09:16:48.393985	2025-10-26 09:16:48.393985	t	t	2
454	ВГ0В-000086	15	72	2	15999.60	2025-09-05 00:00:00	2025-09-05 00:00:00	PAID	t	f	Модуль  дя 1с "Аналоги" для отдела продаж	Шикунов Евгений	2025-10-26 09:16:48.393988	2025-10-26 09:16:48.393989	t	t	2
455	0В0В-003393	41	85	1	10000.00	2025-09-08 00:00:00	2025-09-08 00:00:00	PAID	t	f	для Честного знака	Шикунов Евгений	2025-10-26 09:16:48.393989	2025-10-26 09:16:48.39399	t	t	2
457	ВГ0В-000099	41	72	2	6000.00	2025-09-09 00:00:00	2025-09-09 00:00:00	PAID	t	f	Отчет по ЗУП	Шикунов Евгений	2025-10-26 09:16:48.393992	2025-10-26 09:16:48.393993	t	t	2
458	ВЛ0В-000072	29	61	2	40886.00	2025-09-11 00:00:00	2025-09-11 00:00:00	PAID	t	f	Оплата за сканеры на склад	Шикунов Евгений	2025-10-26 09:16:48.393994	2025-10-26 09:16:48.393994	t	t	2
459	ВГ0В-000102	42	60	2	162616.00	2025-09-11 00:00:00	2025-09-11 00:00:00	PAID	t	f	ситилинк. техника	Шикунов Евгений	2025-10-26 09:16:48.393995	2025-10-26 09:16:48.393996	t	t	2
466	ВГ0В-000112	42	87	2	20411.00	2025-09-12 00:00:00	2025-09-12 00:00:00	PAID	t	f	Оплата электроники, телефоны	Шикунов Евгений	2025-10-26 09:16:48.394005	2025-10-26 09:16:48.394006	t	t	2
430	ВГ0В-000244	12	64	2	8197.08	2025-10-22 21:00:00	2025-10-22 21:00:00	PAID	t	f	Услуги связи	Шикунов Евгений	2025-10-26 09:16:48.393953	2025-10-26 09:32:20.533616	t	t	2
419	ВГ0В-000203	17	68	2	149000.00	2025-10-12 21:00:00	2025-10-12 21:00:00	PAID	t	f	Разработка приложения визитной активности	Шикунов Евгений	2025-10-26 09:16:48.393938	2025-10-26 09:35:36.369972	t	t	2
461	ВЛ0В-000073	12	64	2	16043.04	2025-09-10 21:00:00	2025-09-10 21:00:00	PAID	t	f	\N	Шикунов Евгений	2025-10-26 09:16:48.393998	2025-10-26 09:41:13.170744	t	t	2
460	0М0В-000005	12	64	2	2649.44	2025-09-10 21:00:00	2025-09-10 21:00:00	PAID	t	f	Услуги связи	Шикунов Евгений	2025-10-26 09:16:48.393996	2025-10-26 09:41:19.001883	t	t	2
463	0А0В-000010	12	64	2	25190.78	2025-09-10 21:00:00	2025-09-10 21:00:00	PAID	t	f	Услуги связи	Шикунов Евгений	2025-10-26 09:16:48.394001	2025-10-26 09:41:25.080861	t	t	2
462	ВС0В-000737	12	64	2	959.76	2025-09-10 21:00:00	2025-09-10 21:00:00	PAID	t	f	Услуги связи	Шикунов Евгений	2025-10-26 09:16:48.393999	2025-10-26 09:41:32.21979	t	t	2
464	ВГ0В-000104	12	64	2	7222.66	2025-09-10 21:00:00	2025-09-10 21:00:00	PAID	t	f	Услуги связи	Шикунов Евгений	2025-10-26 09:16:48.394002	2025-10-26 09:41:40.560339	t	t	2
465	0В0В-003454	12	64	1	27743.33	2025-09-10 21:00:00	2025-09-10 21:00:00	PAID	t	f	\N	Шикунов Евгений	2025-10-26 09:16:48.394004	2025-10-26 09:41:48.086276	t	t	2
467	ВГ0В-000113	15	76	2	80000.00	2025-09-11 21:00:00	2025-09-11 21:00:00	PAID	t	f	1с доработки интеграции торгового эквайринга	Шикунов Евгений	2025-10-26 09:16:48.394006	2025-10-26 09:51:14.69481	t	t	2
453	ВГ0В-000085	16	77	2	40000.00	2025-09-03 21:00:00	2025-09-03 21:00:00	PAID	t	f	Аналитик даных	Шикунов Евгений	2025-10-26 09:16:48.393986	2025-10-26 10:06:22.59192	t	t	2
456	ВГ0В-000093	19	59	2	12100.00	2025-09-07 21:00:00	2025-09-07 21:00:00	PAID	t	f	Обслуживвание орг техники	Шикунов Евгений	2025-10-26 09:16:48.393991	2025-10-26 10:11:33.242198	t	t	2
\.


--
-- Data for Name: forecast_expenses; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.forecast_expenses (id, category_id, contractor_id, organization_id, forecast_date, amount, comment, is_regular, based_on_expense_id, created_at, updated_at, department_id) FROM stdin;
166	19	59	2	2025-11-13	17233.33	Автоматически: регулярный расход (среднее за 3 месяца, обычно ~13 числа)	t	\N	2025-10-26 10:21:23.099913	2025-10-26 10:21:23.099916	2
167	15	67	2	2025-11-06	169000.00	Автоматически: регулярный расход (среднее за 3 месяца, обычно ~6 числа)	t	\N	2025-10-26 10:21:23.099918	2025-10-26 10:21:23.09992	2
168	42	60	2	2025-11-07	110242.33	Автоматически: регулярный расход (среднее за 3 месяца, обычно ~10 числа)	t	\N	2025-10-26 10:21:23.099922	2025-10-26 10:21:23.099924	2
169	16	77	2	2025-11-05	40000.00	Автоматически: регулярный расход (среднее за 3 месяца, обычно ~5 числа)	t	\N	2025-10-26 10:21:23.099926	2025-10-26 10:21:23.099928	2
170	41	69	1	2025-11-20	2811.11	Автоматически: регулярный расход (среднее за 3 месяца, обычно ~20 числа)	t	\N	2025-10-26 10:21:23.09993	2025-10-26 10:21:23.099932	2
171	14	78	2	2025-11-14	151375.00	Автоматически: регулярный расход (среднее за 3 месяца, обычно ~14 числа)	t	\N	2025-10-26 10:21:23.099934	2025-10-26 10:21:23.099936	2
172	41	72	2	2025-11-20	3333.33	Автоматически: регулярный расход (среднее за 3 месяца, обычно ~20 числа)	t	\N	2025-10-26 10:21:23.099938	2025-10-26 10:21:23.09994	2
173	12	64	2	2025-11-14	15292.61	Автоматически: регулярный расход (среднее за 3 месяца, обычно ~15 числа)	t	\N	2025-10-26 10:21:23.099942	2025-10-26 10:21:23.099943	2
175	12	\N	2	2025-11-14	17394.06	Автоматически: средний расход по категории (13 раз за 6 мес., обычно ~14 числа)	f	\N	2025-10-26 10:21:23.099949	2025-10-26 10:21:23.099951	2
181	41	\N	2	2025-11-19	2550.00	Автоматически: средний расход по категории (4 раз за 6 мес., обычно ~19 числа)	f	\N	2025-10-26 10:21:23.099972	2025-10-26 10:21:23.099974	2
183	10	\N	1	2025-11-14	13438.50	Автоматически: средний расход по категории (2 раз за 6 мес., обычно ~15 числа)	f	\N	2025-10-26 10:21:23.09998	2025-10-26 10:21:23.099982	2
184	36	\N	1	2025-11-14	231410.00	Автоматически: средний расход по категории (2 раз за 6 мес., обычно ~15 числа)	f	\N	2025-10-26 10:21:23.099984	2025-10-26 10:21:23.099986	2
185	41	\N	1	2025-11-20	18905.56	Автоматически: средний расход по категории (6 раз за 6 мес., обычно ~20 числа)	f	\N	2025-10-26 10:21:23.099988	2025-10-26 10:21:23.099989	2
187	12	\N	1	2025-11-17	67462.07	Автоматически: средний расход по категории (9 раз за 6 мес., обычно ~17 числа)	f	\N	2025-10-26 10:21:23.099995	2025-10-26 10:21:23.099997	2
200	15	76	1	2025-11-14	22025.00	Автоматически: средний расход по категории (2 раз за 6 мес., обычно ~14 числа)	f	\N	2025-10-26 10:21:23.100047	2025-10-26 19:17:27.02137	2
165	10	70	2	2025-11-07	8000.00	Автоматически: регулярный расход (среднее за 3 месяца, обычно ~9 числа)	t	\N	2025-10-26 10:21:23.099902	2025-10-26 10:31:58.562459	2
201	43	73	2	2025-11-03	400000.00	Приложение расшифровки	f	\N	2025-10-26 19:08:15.024533	2025-10-26 19:08:15.024541	2
174	27	60	1	2025-11-14	22361.00	Автоматически: средний расход по категории (2 раз за 6 мес., обычно ~15 числа)	f	\N	2025-10-26 10:21:23.099945	2025-10-26 19:13:12.218092	2
176	24	81	2	2025-11-07	40000.00	Автоматически: средний расход по категории (3 раз за 6 мес., обычно ~10 числа)	f	\N	2025-10-26 10:21:23.099953	2025-10-26 19:13:21.735053	2
177	21	59	1	2025-11-14	21325.00	Автоматически: средний расход по категории (2 раз за 6 мес., обычно ~15 числа)	f	\N	2025-10-26 10:21:23.099957	2025-10-26 19:15:40.41156	2
188	17	68	1	2025-11-14	175000.00	Автоматически: средний расход по категории (2 раз за 6 мес., обычно ~14 числа)	f	\N	2025-10-26 10:21:23.099999	2025-10-26 19:15:59.203796	2
192	20	59	2	2025-11-14	25550.00	Автоматически: средний расход по категории (2 раз за 6 мес., обычно ~14 числа)	f	\N	2025-10-26 10:21:23.100015	2025-10-26 19:16:06.028802	2
194	13	75	2	2025-11-14	50000.00	Автоматически: средний расход по категории (2 раз за 6 мес., обычно ~14 числа)	f	\N	2025-10-26 10:21:23.100023	2025-10-26 19:16:20.185787	2
196	10	\N	2	2025-11-07	3000.00	Интеграция ТГ и MAX	f	\N	2025-10-26 10:21:23.100031	2025-10-26 19:17:10.650012	2
179	11	66	1	2025-11-14	10000.00	Автоматически: средний расход по категории (4 раз за 6 мес., обычно ~14 числа)	f	\N	2025-10-26 10:21:23.099964	2025-10-26 19:17:20.223478	2
198	20	59	1	2025-11-14	14400.00	Автоматически: средний расход по категории (2 раз за 6 мес., обычно ~15 числа)	f	\N	2025-10-26 10:21:23.100039	2025-10-26 19:17:35.465171	2
197	26	60	1	2025-11-14	90540.00	Автоматически: средний расход по категории (2 раз за 6 мес., обычно ~15 числа)	f	\N	2025-10-26 10:21:23.100035	2025-10-26 19:17:41.176237	2
199	42	60	1	2025-11-11	31400.00	Автоматически: средний расход по категории (3 раз за 6 мес., обычно ~11 числа)	f	\N	2025-10-26 10:21:23.100043	2025-10-26 19:18:11.383654	2
193	42	60	2	2025-11-14	70740.00	Автоматически: средний расход по категории (18 раз за 6 мес., обычно ~14 числа)	f	\N	2025-10-26 10:21:23.100019	2025-10-26 19:18:16.973008	2
190	19	86	2	2025-11-19	23833.33	Автоматически: средний расход по категории (6 раз за 6 мес., обычно ~19 числа)	f	\N	2025-10-26 10:21:23.100007	2025-10-26 19:18:26.566392	2
202	10	70	2	2025-12-09	4000.00	Автоматически: регулярный расход (среднее за 3 месяца, обычно ~9 числа)	t	\N	2025-10-27 11:16:14.31844	2025-10-27 11:16:14.318443	2
203	19	59	2	2025-12-12	17233.33	Автоматически: регулярный расход (среднее за 3 месяца, обычно ~13 числа)	t	\N	2025-10-27 11:16:14.318444	2025-10-27 11:16:14.318445	2
204	42	60	2	2025-12-08	72672.75	Автоматически: регулярный расход (среднее за 3 месяца, обычно ~8 числа)	t	\N	2025-10-27 11:16:14.318446	2025-10-27 11:16:14.318447	2
205	41	69	1	2025-12-22	2783.34	Автоматически: регулярный расход (среднее за 3 месяца, обычно ~22 числа)	t	\N	2025-10-27 11:16:14.318448	2025-10-27 11:16:14.318448	2
206	41	72	2	2025-12-19	3333.33	Автоматически: регулярный расход (среднее за 3 месяца, обычно ~20 числа)	t	\N	2025-10-27 11:16:14.318449	2025-10-27 11:16:14.31845	2
207	12	64	2	2025-12-12	11697.87	Автоматически: регулярный расход (среднее за 3 месяца, обычно ~14 числа)	t	\N	2025-10-27 11:16:14.318451	2025-10-27 11:16:14.318451	2
208	12	\N	2	2025-12-12	14573.56	Автоматически: средний расход по категории (12 раз за 6 мес., обычно ~14 числа)	f	\N	2025-10-27 11:16:14.318452	2025-10-27 11:16:14.318453	2
209	24	\N	2	2025-12-09	40000.00	Автоматически: средний расход по категории (3 раз за 6 мес., обычно ~10 числа)	f	\N	2025-10-27 11:16:14.318454	2025-10-27 11:16:14.318454	2
210	14	\N	2	2025-12-17	134071.43	Автоматически: средний расход по категории (7 раз за 6 мес., обычно ~17 числа)	f	\N	2025-10-27 11:16:14.318455	2025-10-27 11:16:14.318456	2
211	11	\N	1	2025-12-12	8666.67	Автоматически: средний расход по категории (3 раз за 6 мес., обычно ~13 числа)	f	\N	2025-10-27 11:16:14.318456	2025-10-27 11:16:14.318457	2
212	15	\N	2	2025-12-05	113142.80	Автоматически: средний расход по категории (7 раз за 6 мес., обычно ~6 числа)	f	\N	2025-10-27 11:16:14.318458	2025-10-27 11:16:14.318458	2
213	41	\N	2	2025-12-19	2550.00	Автоматически: средний расход по категории (4 раз за 6 мес., обычно ~19 числа)	f	\N	2025-10-27 11:16:14.318459	2025-10-27 11:16:14.31846	2
214	23	\N	2	2025-12-12	44400.00	Автоматически: средний расход по категории (2 раз за 6 мес., обычно ~12 числа)	f	\N	2025-10-27 11:16:14.31846	2025-10-27 11:16:14.318461	2
215	17	\N	2	2025-12-19	141333.33	Автоматически: средний расход по категории (3 раз за 6 мес., обычно ~19 числа)	f	\N	2025-10-27 11:16:14.318462	2025-10-27 11:16:14.318462	2
216	41	\N	1	2025-12-19	16590.48	Автоматически: средний расход по категории (7 раз за 6 мес., обычно ~21 числа)	f	\N	2025-10-27 11:16:14.318463	2025-10-27 11:16:14.318464	2
217	12	\N	1	2025-12-18	60634.86	Автоматически: средний расход по категории (10 раз за 6 мес., обычно ~18 числа)	f	\N	2025-10-27 11:16:14.318465	2025-10-27 11:16:14.318465	2
218	9	\N	2	2025-12-22	68710.00	Автоматически: средний расход по категории (2 раз за 6 мес., обычно ~22 числа)	f	\N	2025-10-27 11:16:14.318466	2025-10-27 11:16:14.318467	2
219	19	\N	2	2025-12-19	23833.33	Автоматически: средний расход по категории (6 раз за 6 мес., обычно ~19 числа)	f	\N	2025-10-27 11:16:14.318467	2025-10-27 11:16:14.318468	2
220	20	\N	2	2025-12-12	25550.00	Автоматически: средний расход по категории (2 раз за 6 мес., обычно ~14 числа)	f	\N	2025-10-27 11:16:14.318469	2025-10-27 11:16:14.318469	2
221	42	\N	2	2025-12-15	44767.72	Автоматически: средний расход по категории (18 раз за 6 мес., обычно ~15 числа)	f	\N	2025-10-27 11:16:14.31847	2025-10-27 11:16:14.318471	2
222	13	\N	2	2025-12-12	50000.00	Автоматически: средний расход по категории (2 раз за 6 мес., обычно ~14 числа)	f	\N	2025-10-27 11:16:14.318471	2025-10-27 11:16:14.318472	2
223	16	\N	2	2025-12-12	40000.00	Автоматически: средний расход по категории (5 раз за 6 мес., обычно ~12 числа)	f	\N	2025-10-27 11:16:14.318473	2025-10-27 11:16:14.318473	2
224	10	\N	2	2025-12-09	4000.00	Автоматически: средний расход по категории (3 раз за 6 мес., обычно ~9 числа)	f	\N	2025-10-27 11:16:14.318474	2025-10-27 11:16:14.318475	2
225	42	\N	1	2025-12-11	31400.00	Автоматически: средний расход по категории (3 раз за 6 мес., обычно ~11 числа)	f	\N	2025-10-27 11:16:14.318475	2025-10-27 11:16:14.318476	2
\.


--
-- Data for Name: kpi_goals; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.kpi_goals (id, name, description, category, metric_name, metric_unit, target_value, weight, year, is_annual, status, department_id, created_at, updated_at) FROM stdin;
1	Кассы	\N	\N	\N	\N	\N	100.00	2025	t	ACTIVE	2	2025-10-28 21:54:43.010726	2025-10-28 21:54:43.010731
\.


--
-- Data for Name: organizations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.organizations (id, name, legal_name, is_active, created_at, updated_at, department_id) FROM stdin;
2	ВЕСТ ГРУПП ООО	Общество с ограниченной ответственностью ВЕСТ ГРУПП	t	2025-10-25 15:59:38.294473	2025-10-25 15:59:38.294474	1
1	ВЕСТ ООО	Общество с ограниченной ответственностью ВЕСТ	t	2025-10-25 15:59:38.29447	2025-10-25 17:04:16.536822	2
4	ООО "АРТБГ"	\N	t	2025-10-27 08:55:18.012528	2025-10-27 08:55:18.012535	2
\.


--
-- Data for Name: payroll_actuals; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payroll_actuals (id, year, month, employee_id, department_id, base_salary_paid, other_payments_paid, total_paid, payment_date, expense_id, notes, created_at, updated_at, monthly_bonus_paid, quarterly_bonus_paid, annual_bonus_paid, income_tax_rate, income_tax_amount, social_tax_amount) FROM stdin;
1	2025	10	1	2	150000.00	0.00	150000.00	2025-10-25	\N	Аванс за 10.2025	2025-10-28 21:17:07.99755	2025-10-28 21:17:07.997557	0.00	0.00	0.00	0.1300	0.00	0.00
2	2025	10	2	2	50000.00	0.00	50000.00	2025-10-25	\N	Аванс за 10.2025	2025-10-28 21:17:07.99756	2025-10-28 21:17:07.997561	0.00	0.00	0.00	0.1300	0.00	0.00
3	2025	10	3	2	80000.00	0.00	80000.00	2025-10-25	\N	Аванс за 10.2025	2025-10-28 21:17:07.997563	2025-10-28 21:17:07.997564	0.00	0.00	0.00	0.1300	0.00	0.00
4	2025	10	4	2	90000.00	0.00	90000.00	2025-10-25	\N	Аванс за 10.2025	2025-10-28 21:17:07.997565	2025-10-28 21:17:07.997566	0.00	0.00	0.00	0.1300	0.00	0.00
5	2025	10	5	2	150000.00	0.00	150000.00	2025-10-25	\N	Аванс за 10.2025	2025-10-28 21:17:07.997568	2025-10-28 21:17:07.997569	0.00	0.00	0.00	0.1300	0.00	0.00
6	2025	10	6	2	60000.00	0.00	60000.00	2025-10-25	\N	Аванс за 10.2025	2025-10-28 21:17:07.99757	2025-10-28 21:17:07.997571	0.00	0.00	0.00	0.1300	0.00	0.00
7	2025	10	7	2	30000.00	0.00	30000.00	2025-10-25	\N	Аванс за 10.2025	2025-10-28 21:17:07.997573	2025-10-28 21:17:07.997574	0.00	0.00	0.00	0.1300	0.00	0.00
8	2025	9	1	2	150000.00	0.00	341590.00	2025-09-10	\N	Массовая регистрация выплат за 09.2025	2025-10-28 22:15:37.165119	2025-10-28 22:15:37.165125	56350.00	135240.00	0.00	0.1300	0.00	0.00
9	2025	9	2	2	50000.00	0.00	101000.00	2025-09-10	\N	Массовая регистрация выплат за 09.2025	2025-10-28 22:15:37.165126	2025-10-28 22:15:37.165127	15000.00	36000.00	0.00	0.1300	0.00	0.00
10	2025	9	3	2	80000.00	0.00	176000.00	2025-09-10	\N	Массовая регистрация выплат за 09.2025	2025-10-28 22:15:37.165129	2025-10-28 22:15:37.16513	48000.00	48000.00	0.00	0.1300	0.00	0.00
11	2025	9	4	2	90000.00	0.00	195400.00	2025-09-10	\N	Массовая регистрация выплат за 09.2025	2025-10-28 22:15:37.165131	2025-10-28 22:15:37.165132	31000.00	74400.00	0.00	0.1300	0.00	0.00
12	2025	9	5	2	150000.00	0.00	350000.00	2025-09-10	\N	Массовая регистрация выплат за 09.2025	2025-10-28 22:15:37.165133	2025-10-28 22:15:37.165134	200000.00	0.00	0.00	0.1300	0.00	0.00
13	2025	9	7	2	30000.00	0.00	166000.00	2025-09-10	\N	Массовая регистрация выплат за 09.2025	2025-10-28 22:15:37.165135	2025-10-28 22:15:37.165136	40000.00	96000.00	0.00	0.1300	0.00	0.00
14	2025	10	1	2	150000.00	0.00	206350.00	2025-10-10	\N	Массовая регистрация выплат за 10.2025	2025-10-28 22:52:02.114352	2025-10-28 22:52:02.114356	56350.00	0.00	0.00	0.1300	0.00	0.00
15	2025	10	2	2	50000.00	0.00	65000.00	2025-10-10	\N	Массовая регистрация выплат за 10.2025	2025-10-28 22:52:02.114358	2025-10-28 22:52:02.114359	15000.00	0.00	0.00	0.1300	0.00	0.00
16	2025	10	3	2	80000.00	0.00	128000.00	2025-10-10	\N	Массовая регистрация выплат за 10.2025	2025-10-28 22:52:02.11436	2025-10-28 22:52:02.114361	48000.00	0.00	0.00	0.1300	0.00	0.00
17	2025	10	4	2	90000.00	0.00	121000.00	2025-10-10	\N	Массовая регистрация выплат за 10.2025	2025-10-28 22:52:02.114362	2025-10-28 22:52:02.114364	31000.00	0.00	0.00	0.1300	0.00	0.00
18	2025	10	5	2	150000.00	0.00	350000.00	2025-10-10	\N	Массовая регистрация выплат за 10.2025	2025-10-28 22:52:02.114364	2025-10-28 22:52:02.114365	200000.00	0.00	0.00	0.1300	0.00	0.00
19	2025	10	6	2	60000.00	0.00	60000.00	2025-10-10	\N	Массовая регистрация выплат за 10.2025	2025-10-28 22:52:02.114367	2025-10-28 22:52:02.114368	0.00	0.00	0.00	0.1300	0.00	0.00
20	2025	10	7	2	30000.00	0.00	70000.00	2025-10-10	\N	Массовая регистрация выплат за 10.2025	2025-10-28 22:52:02.114369	2025-10-28 22:52:02.11437	40000.00	0.00	0.00	0.1300	0.00	0.00
\.


--
-- Data for Name: payroll_plans; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payroll_plans (id, year, month, employee_id, department_id, base_salary, other_payments, total_planned, notes, created_at, updated_at, monthly_bonus, quarterly_bonus, annual_bonus) FROM stdin;
88	2025	4	1	2	300000.00	0.00	400000.00	\N	2025-10-25 17:04:39.025902	2025-10-28 21:56:39.572414	100000.00	0.00	0.00
85	2025	1	1	2	300000.00	0.00	356350.00	\N	2025-10-25 17:04:39.025895	2025-10-25 17:04:39.025898	56350.00	0.00	0.00
86	2025	2	1	2	300000.00	0.00	356350.00	\N	2025-10-25 17:04:39.025899	2025-10-25 17:04:39.0259	56350.00	0.00	0.00
89	2025	5	1	2	300000.00	0.00	356350.00	\N	2025-10-25 17:04:39.025904	2025-10-25 17:04:39.025905	56350.00	0.00	0.00
87	2025	3	1	2	300000.00	0.00	491590.00	\N	2025-10-25 17:04:39.025901	2025-10-25 17:04:39.025902	56350.00	135240.00	0.00
90	2025	6	1	2	300000.00	0.00	491590.00	\N	2025-10-25 17:04:39.025905	2025-10-25 17:04:39.025906	56350.00	135240.00	0.00
114	2025	6	3	2	160000.00	0.00	256000.00	\N	2025-10-25 17:04:39.025939	2025-10-25 17:04:39.025939	48000.00	48000.00	0.00
108	2025	12	2	2	100000.00	0.00	187000.00	\N	2025-10-25 17:04:39.02593	2025-10-25 17:04:39.025931	15000.00	36000.00	36000.00
115	2025	7	3	2	160000.00	0.00	208000.00	\N	2025-10-25 17:04:39.02594	2025-10-25 17:04:39.025941	48000.00	0.00	0.00
117	2025	9	3	2	160000.00	0.00	256000.00	\N	2025-10-25 17:04:39.025943	2025-10-25 17:04:39.025943	48000.00	48000.00	0.00
123	2025	3	4	2	180000.00	0.00	285400.00	\N	2025-10-25 17:04:39.025951	2025-10-25 17:04:39.025952	31000.00	74400.00	0.00
126	2025	6	4	2	180000.00	0.00	285400.00	\N	2025-10-25 17:04:39.025955	2025-10-25 17:04:39.025956	31000.00	74400.00	0.00
129	2025	9	4	2	180000.00	0.00	285400.00	\N	2025-10-25 17:04:39.025959	2025-10-25 17:04:39.02596	31000.00	74400.00	0.00
138	2025	6	5	2	300000.00	0.00	500000.00	\N	2025-10-25 17:04:39.025972	2025-10-25 17:04:39.025972	200000.00	0.00	0.00
141	2025	9	5	2	300000.00	0.00	500000.00	\N	2025-10-25 17:04:39.025976	2025-10-25 17:04:39.025977	200000.00	0.00	0.00
159	2025	3	7	2	60000.00	0.00	196000.00	\N	2025-10-25 17:04:39.026001	2025-10-25 17:04:39.026001	40000.00	96000.00	0.00
162	2025	6	7	2	60000.00	0.00	196000.00	\N	2025-10-25 17:04:39.026005	2025-10-25 17:04:39.026005	40000.00	96000.00	0.00
165	2025	9	7	2	60000.00	0.00	196000.00	\N	2025-10-25 17:04:39.026009	2025-10-25 17:04:39.026009	40000.00	96000.00	0.00
116	2025	8	3	2	160000.00	0.00	208000.00	\N	2025-10-25 17:04:39.025941	2025-10-25 17:04:39.025942	48000.00	0.00	0.00
118	2025	10	3	2	160000.00	0.00	208000.00	\N	2025-10-25 17:04:39.025944	2025-10-25 17:04:39.025945	48000.00	0.00	0.00
119	2025	11	3	2	160000.00	0.00	208000.00	\N	2025-10-25 17:04:39.025946	2025-10-25 17:04:39.025946	48000.00	0.00	0.00
136	2025	4	5	2	300000.00	0.00	400000.00	\N	2025-10-25 17:04:39.025969	2025-10-28 21:56:56.992013	100000.00	0.00	0.00
137	2025	5	5	2	300000.00	0.00	400000.00	\N	2025-10-25 17:04:39.02597	2025-10-28 22:21:11.360879	100000.00	0.00	0.00
122	2025	2	4	2	180000.00	0.00	211000.00	\N	2025-10-25 17:04:39.02595	2025-10-25 17:04:39.02595	31000.00	0.00	0.00
124	2025	4	4	2	180000.00	0.00	211000.00	\N	2025-10-25 17:04:39.025952	2025-10-25 17:04:39.025953	31000.00	0.00	0.00
125	2025	5	4	2	180000.00	0.00	211000.00	\N	2025-10-25 17:04:39.025954	2025-10-25 17:04:39.025954	31000.00	0.00	0.00
127	2025	7	4	2	180000.00	0.00	211000.00	\N	2025-10-25 17:04:39.025956	2025-10-25 17:04:39.025957	31000.00	0.00	0.00
128	2025	8	4	2	180000.00	0.00	211000.00	\N	2025-10-25 17:04:39.025958	2025-10-25 17:04:39.025958	31000.00	0.00	0.00
130	2025	10	4	2	180000.00	0.00	211000.00	\N	2025-10-25 17:04:39.025961	2025-10-25 17:04:39.025961	31000.00	0.00	0.00
131	2025	11	4	2	180000.00	0.00	211000.00	\N	2025-10-25 17:04:39.025962	2025-10-25 17:04:39.025963	31000.00	0.00	0.00
139	2025	7	5	2	300000.00	0.00	500000.00	\N	2025-10-25 17:04:39.025973	2025-10-25 17:04:39.025974	200000.00	0.00	0.00
140	2025	8	5	2	300000.00	0.00	500000.00	\N	2025-10-25 17:04:39.025975	2025-10-25 17:04:39.025975	200000.00	0.00	0.00
142	2025	10	5	2	300000.00	0.00	500000.00	\N	2025-10-25 17:04:39.025977	2025-10-25 17:04:39.025978	200000.00	0.00	0.00
143	2025	11	5	2	300000.00	0.00	500000.00	\N	2025-10-25 17:04:39.025979	2025-10-25 17:04:39.025979	200000.00	0.00	0.00
157	2025	1	7	2	60000.00	0.00	100000.00	\N	2025-10-25 17:04:39.025998	2025-10-25 17:04:39.025999	40000.00	0.00	0.00
158	2025	2	7	2	60000.00	0.00	100000.00	\N	2025-10-25 17:04:39.025999	2025-10-25 17:04:39.026	40000.00	0.00	0.00
160	2025	4	7	2	60000.00	0.00	100000.00	\N	2025-10-25 17:04:39.026002	2025-10-25 17:04:39.026003	40000.00	0.00	0.00
161	2025	5	7	2	60000.00	0.00	100000.00	\N	2025-10-25 17:04:39.026003	2025-10-25 17:04:39.026004	40000.00	0.00	0.00
163	2025	7	7	2	60000.00	0.00	100000.00	\N	2025-10-25 17:04:39.026006	2025-10-25 17:04:39.026007	40000.00	0.00	0.00
164	2025	8	7	2	60000.00	0.00	100000.00	\N	2025-10-25 17:04:39.026007	2025-10-25 17:04:39.026008	40000.00	0.00	0.00
166	2025	10	7	2	60000.00	0.00	100000.00	\N	2025-10-25 17:04:39.02601	2025-10-25 17:04:39.026011	40000.00	0.00	0.00
167	2025	11	7	2	60000.00	0.00	100000.00	\N	2025-10-25 17:04:39.026012	2025-10-25 17:04:39.026012	40000.00	0.00	0.00
97	2025	1	2	2	100000.00	0.00	115000.00	\N	2025-10-25 17:04:39.025915	2025-10-25 17:04:39.025916	15000.00	0.00	0.00
98	2025	2	2	2	100000.00	0.00	115000.00	\N	2025-10-25 17:04:39.025917	2025-10-25 17:04:39.025917	15000.00	0.00	0.00
120	2025	12	3	2	160000.00	0.00	304000.00	\N	2025-10-25 17:04:39.025947	2025-10-25 17:04:39.025948	48000.00	48000.00	48000.00
135	2025	3	5	2	300000.00	0.00	500000.00	\N	2025-10-25 17:04:39.025967	2025-10-25 17:04:39.025968	200000.00	0.00	0.00
132	2025	12	4	2	180000.00	0.00	359800.00	\N	2025-10-25 17:04:39.025963	2025-10-25 17:04:39.025964	31000.00	74400.00	74400.00
144	2025	12	5	2	300000.00	0.00	500000.00	\N	2025-10-25 17:04:39.02598	2025-10-25 17:04:39.025981	200000.00	0.00	0.00
168	2025	12	7	2	60000.00	0.00	244000.00	\N	2025-10-25 17:04:39.026013	2025-10-25 17:04:39.026014	40000.00	96000.00	48000.00
154	2025	10	6	2	120000.00	0.00	120000.00	\N	2025-10-25 17:04:39.025994	2025-10-25 17:04:39.025995	0.00	0.00	0.00
155	2025	11	6	2	120000.00	0.00	120000.00	\N	2025-10-25 17:04:39.025995	2025-10-25 17:04:39.025996	0.00	0.00	0.00
100	2025	4	2	2	100000.00	0.00	115000.00	\N	2025-10-25 17:04:39.025919	2025-10-25 17:04:39.02592	15000.00	0.00	0.00
101	2025	5	2	2	100000.00	0.00	115000.00	\N	2025-10-25 17:04:39.025921	2025-10-25 17:04:39.025921	15000.00	0.00	0.00
103	2025	7	2	2	100000.00	0.00	115000.00	\N	2025-10-25 17:04:39.025923	2025-10-25 17:04:39.025924	15000.00	0.00	0.00
104	2025	8	2	2	100000.00	0.00	115000.00	\N	2025-10-25 17:04:39.025925	2025-10-25 17:04:39.025926	15000.00	0.00	0.00
91	2025	7	1	2	300000.00	0.00	356350.00	\N	2025-10-25 17:04:39.025907	2025-10-25 17:04:39.025908	56350.00	0.00	0.00
92	2025	8	1	2	300000.00	0.00	356350.00	\N	2025-10-25 17:04:39.025908	2025-10-25 17:04:39.025909	56350.00	0.00	0.00
94	2025	10	1	2	300000.00	0.00	356350.00	\N	2025-10-25 17:04:39.025911	2025-10-25 17:04:39.025912	56350.00	0.00	0.00
95	2025	11	1	2	300000.00	0.00	356350.00	\N	2025-10-25 17:04:39.025913	2025-10-25 17:04:39.025913	56350.00	0.00	0.00
106	2025	10	2	2	100000.00	0.00	115000.00	\N	2025-10-25 17:04:39.025928	2025-10-25 17:04:39.025928	15000.00	0.00	0.00
107	2025	11	2	2	100000.00	0.00	115000.00	\N	2025-10-25 17:04:39.025929	2025-10-25 17:04:39.02593	15000.00	0.00	0.00
99	2025	3	2	2	100000.00	0.00	151000.00	\N	2025-10-25 17:04:39.025918	2025-10-25 17:04:39.025919	15000.00	36000.00	0.00
102	2025	6	2	2	100000.00	0.00	151000.00	\N	2025-10-25 17:04:39.025922	2025-10-25 17:04:39.025923	15000.00	36000.00	0.00
93	2025	9	1	2	300000.00	0.00	491590.00	\N	2025-10-25 17:04:39.02591	2025-10-25 17:04:39.02591	56350.00	135240.00	0.00
105	2025	9	2	2	100000.00	0.00	151000.00	\N	2025-10-25 17:04:39.025926	2025-10-25 17:04:39.025927	15000.00	36000.00	0.00
156	2025	12	6	2	120000.00	0.00	120000.00	\N	2025-10-25 17:04:39.025997	2025-10-25 17:04:39.025997	0.00	0.00	0.00
96	2025	12	1	2	300000.00	0.00	559210.00	\N	2025-10-25 17:04:39.025914	2025-10-25 17:04:39.025915	56350.00	135240.00	67620.00
\.


--
-- Data for Name: salary_history; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.salary_history (id, employee_id, old_salary, new_salary, effective_date, reason, notes, created_at) FROM stdin;
1	1	400000.00	300000.00	2025-10-26	Salary adjustment	Updated via employee edit	2025-10-26 09:33:37.208065
2	8	\N	180000.00	2025-01-15	Initial hire	Created during employee registration	2025-10-27 07:36:34.323231
6	5	0.00	300000.00	2025-10-27	Salary adjustment	Updated via employee edit	2025-10-27 08:00:24.573067
7	3	0.00	160000.00	2025-10-27	Salary adjustment	Updated via employee edit	2025-10-27 08:06:02.475239
8	4	230000.00	180000.00	2025-10-27	Salary adjustment	Updated via employee edit	2025-10-27 08:07:38.303657
9	6	0.00	120000.00	2025-10-27	Salary adjustment	Updated via employee edit	2025-10-27 08:08:32.131474
10	7	0.00	60000.00	2025-10-27	Salary adjustment	Updated via employee edit	2025-10-27 08:09:45.040913
11	8	180000.00	0.00	2025-10-27	Salary adjustment	Updated via employee edit	2025-10-27 08:12:24.982081
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, username, email, full_name, hashed_password, role, is_active, is_verified, "position", phone, last_login, created_at, updated_at, department_id) FROM stdin;
1	admin	admin@example.com	System Administrator	$2b$12$.IVjOLZ1MCrvvt86P1yPEOxfb8oRsyZ6e8.pZncRr/7fngwRoH9PG	ADMIN	t	t	Administrator		2025-10-28 22:50:34.617178	2025-10-25 15:59:38.949922	2025-10-28 22:50:34.617985	2
\.


--
-- Name: attachments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.attachments_id_seq', 1, false);


--
-- Name: audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.audit_logs_id_seq', 62, true);


--
-- Name: budget_approval_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.budget_approval_log_id_seq', 1, false);


--
-- Name: budget_categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.budget_categories_id_seq', 45, true);


--
-- Name: budget_plan_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.budget_plan_details_id_seq', 4, true);


--
-- Name: budget_plans_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.budget_plans_id_seq', 566, true);


--
-- Name: budget_scenarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.budget_scenarios_id_seq', 7, true);


--
-- Name: budget_versions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.budget_versions_id_seq', 6, true);


--
-- Name: contractors_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.contractors_id_seq', 91, true);


--
-- Name: dashboard_configs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dashboard_configs_id_seq', 1, false);


--
-- Name: departments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.departments_id_seq', 2, true);


--
-- Name: employee_kpi_goals_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.employee_kpi_goals_id_seq', 1, true);


--
-- Name: employee_kpis_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.employee_kpis_id_seq', 1, true);


--
-- Name: employees_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.employees_id_seq', 11, true);


--
-- Name: expenses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.expenses_id_seq', 513, true);


--
-- Name: forecast_expenses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.forecast_expenses_id_seq', 225, true);


--
-- Name: kpi_goals_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.kpi_goals_id_seq', 1, true);


--
-- Name: organizations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.organizations_id_seq', 4, true);


--
-- Name: payroll_actuals_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.payroll_actuals_id_seq', 20, true);


--
-- Name: payroll_plans_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.payroll_plans_id_seq', 168, true);


--
-- Name: salary_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.salary_history_id_seq', 11, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: attachments attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attachments
    ADD CONSTRAINT attachments_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: budget_approval_log budget_approval_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_approval_log
    ADD CONSTRAINT budget_approval_log_pkey PRIMARY KEY (id);


--
-- Name: budget_categories budget_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_categories
    ADD CONSTRAINT budget_categories_pkey PRIMARY KEY (id);


--
-- Name: budget_plan_details budget_plan_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_plan_details
    ADD CONSTRAINT budget_plan_details_pkey PRIMARY KEY (id);


--
-- Name: budget_plans budget_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_plans
    ADD CONSTRAINT budget_plans_pkey PRIMARY KEY (id);


--
-- Name: budget_scenarios budget_scenarios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_scenarios
    ADD CONSTRAINT budget_scenarios_pkey PRIMARY KEY (id);


--
-- Name: budget_versions budget_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_versions
    ADD CONSTRAINT budget_versions_pkey PRIMARY KEY (id);


--
-- Name: contractors contractors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contractors
    ADD CONSTRAINT contractors_pkey PRIMARY KEY (id);


--
-- Name: dashboard_configs dashboard_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dashboard_configs
    ADD CONSTRAINT dashboard_configs_pkey PRIMARY KEY (id);


--
-- Name: departments departments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (id);


--
-- Name: employee_kpi_goals employee_kpi_goals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_kpi_goals
    ADD CONSTRAINT employee_kpi_goals_pkey PRIMARY KEY (id);


--
-- Name: employee_kpis employee_kpis_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_kpis
    ADD CONSTRAINT employee_kpis_pkey PRIMARY KEY (id);


--
-- Name: employees employees_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_pkey PRIMARY KEY (id);


--
-- Name: expenses expenses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_pkey PRIMARY KEY (id);


--
-- Name: forecast_expenses forecast_expenses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.forecast_expenses
    ADD CONSTRAINT forecast_expenses_pkey PRIMARY KEY (id);


--
-- Name: kpi_goals kpi_goals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kpi_goals
    ADD CONSTRAINT kpi_goals_pkey PRIMARY KEY (id);


--
-- Name: organizations organizations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (id);


--
-- Name: payroll_actuals payroll_actuals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_actuals
    ADD CONSTRAINT payroll_actuals_pkey PRIMARY KEY (id);


--
-- Name: payroll_plans payroll_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_plans
    ADD CONSTRAINT payroll_plans_pkey PRIMARY KEY (id);


--
-- Name: salary_history salary_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.salary_history
    ADD CONSTRAINT salary_history_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_approval_log_version_iteration; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_approval_log_version_iteration ON public.budget_approval_log USING btree (version_id, iteration_number);


--
-- Name: idx_audit_log_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_log_entity ON public.audit_logs USING btree (entity_type, entity_id);


--
-- Name: idx_audit_log_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_log_timestamp ON public.audit_logs USING btree ("timestamp");


--
-- Name: idx_audit_log_user_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_log_user_action ON public.audit_logs USING btree (user_id, action);


--
-- Name: idx_budget_category_dept_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_budget_category_dept_active ON public.budget_categories USING btree (department_id, is_active);


--
-- Name: idx_budget_detail_version_month_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_budget_detail_version_month_category ON public.budget_plan_details USING btree (version_id, month, category_id);


--
-- Name: idx_budget_plan_dept_year_month; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_budget_plan_dept_year_month ON public.budget_plans USING btree (department_id, year, month);


--
-- Name: idx_budget_scenario_year_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_budget_scenario_year_type ON public.budget_scenarios USING btree (year, scenario_type);


--
-- Name: idx_budget_version_dept_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_budget_version_dept_year ON public.budget_versions USING btree (department_id, year);


--
-- Name: idx_budget_version_year_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_budget_version_year_status ON public.budget_versions USING btree (year, status);


--
-- Name: idx_contractor_dept_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_contractor_dept_active ON public.contractors USING btree (department_id, is_active);


--
-- Name: idx_emp_kpi_goal_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_emp_kpi_goal_period ON public.employee_kpi_goals USING btree (employee_id, goal_id, year, month);


--
-- Name: idx_employee_dept_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_employee_dept_status ON public.employees USING btree (department_id, status);


--
-- Name: idx_employee_kpi_dept; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_employee_kpi_dept ON public.employee_kpis USING btree (department_id, year, month);


--
-- Name: idx_employee_kpi_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_employee_kpi_period ON public.employee_kpis USING btree (employee_id, year, month);


--
-- Name: idx_expense_dept_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_expense_dept_date ON public.expenses USING btree (department_id, request_date);


--
-- Name: idx_expense_dept_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_expense_dept_status ON public.expenses USING btree (department_id, status);


--
-- Name: idx_kpi_goal_dept_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_kpi_goal_dept_status ON public.kpi_goals USING btree (department_id, status);


--
-- Name: idx_organization_dept_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_organization_dept_active ON public.organizations USING btree (department_id, is_active);


--
-- Name: idx_payroll_actual_dept_year_month; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payroll_actual_dept_year_month ON public.payroll_actuals USING btree (department_id, year, month);


--
-- Name: idx_payroll_actual_employee_year_month; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payroll_actual_employee_year_month ON public.payroll_actuals USING btree (employee_id, year, month);


--
-- Name: idx_payroll_plan_dept_year_month; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payroll_plan_dept_year_month ON public.payroll_plans USING btree (department_id, year, month);


--
-- Name: idx_payroll_plan_employee_year_month; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payroll_plan_employee_year_month ON public.payroll_plans USING btree (employee_id, year, month);


--
-- Name: idx_salary_history_employee_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_salary_history_employee_date ON public.salary_history USING btree (employee_id, effective_date);


--
-- Name: ix_attachments_expense_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_attachments_expense_id ON public.attachments USING btree (expense_id);


--
-- Name: ix_attachments_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_attachments_id ON public.attachments USING btree (id);


--
-- Name: ix_audit_logs_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_action ON public.audit_logs USING btree (action);


--
-- Name: ix_audit_logs_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_department_id ON public.audit_logs USING btree (department_id);


--
-- Name: ix_audit_logs_entity_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_entity_id ON public.audit_logs USING btree (entity_id);


--
-- Name: ix_audit_logs_entity_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_entity_type ON public.audit_logs USING btree (entity_type);


--
-- Name: ix_audit_logs_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_id ON public.audit_logs USING btree (id);


--
-- Name: ix_audit_logs_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_timestamp ON public.audit_logs USING btree ("timestamp");


--
-- Name: ix_audit_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_user_id ON public.audit_logs USING btree (user_id);


--
-- Name: ix_budget_approval_log_decision_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_approval_log_decision_date ON public.budget_approval_log USING btree (decision_date);


--
-- Name: ix_budget_approval_log_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_approval_log_id ON public.budget_approval_log USING btree (id);


--
-- Name: ix_budget_approval_log_version_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_approval_log_version_id ON public.budget_approval_log USING btree (version_id);


--
-- Name: ix_budget_categories_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_categories_department_id ON public.budget_categories USING btree (department_id);


--
-- Name: ix_budget_categories_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_categories_id ON public.budget_categories USING btree (id);


--
-- Name: ix_budget_categories_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_categories_is_active ON public.budget_categories USING btree (is_active);


--
-- Name: ix_budget_categories_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_categories_name ON public.budget_categories USING btree (name);


--
-- Name: ix_budget_categories_parent_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_categories_parent_id ON public.budget_categories USING btree (parent_id);


--
-- Name: ix_budget_plan_details_calculation_method; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_plan_details_calculation_method ON public.budget_plan_details USING btree (calculation_method);


--
-- Name: ix_budget_plan_details_category_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_plan_details_category_id ON public.budget_plan_details USING btree (category_id);


--
-- Name: ix_budget_plan_details_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_plan_details_id ON public.budget_plan_details USING btree (id);


--
-- Name: ix_budget_plan_details_month; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_plan_details_month ON public.budget_plan_details USING btree (month);


--
-- Name: ix_budget_plan_details_version_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_plan_details_version_id ON public.budget_plan_details USING btree (version_id);


--
-- Name: ix_budget_plans_category_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_plans_category_id ON public.budget_plans USING btree (category_id);


--
-- Name: ix_budget_plans_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_plans_department_id ON public.budget_plans USING btree (department_id);


--
-- Name: ix_budget_plans_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_plans_id ON public.budget_plans USING btree (id);


--
-- Name: ix_budget_plans_month; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_plans_month ON public.budget_plans USING btree (month);


--
-- Name: ix_budget_plans_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_plans_status ON public.budget_plans USING btree (status);


--
-- Name: ix_budget_plans_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_plans_year ON public.budget_plans USING btree (year);


--
-- Name: ix_budget_scenarios_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_scenarios_department_id ON public.budget_scenarios USING btree (department_id);


--
-- Name: ix_budget_scenarios_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_scenarios_id ON public.budget_scenarios USING btree (id);


--
-- Name: ix_budget_scenarios_scenario_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_scenarios_scenario_type ON public.budget_scenarios USING btree (scenario_type);


--
-- Name: ix_budget_scenarios_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_scenarios_year ON public.budget_scenarios USING btree (year);


--
-- Name: ix_budget_versions_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_versions_department_id ON public.budget_versions USING btree (department_id);


--
-- Name: ix_budget_versions_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_versions_id ON public.budget_versions USING btree (id);


--
-- Name: ix_budget_versions_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_versions_scenario_id ON public.budget_versions USING btree (scenario_id);


--
-- Name: ix_budget_versions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_versions_status ON public.budget_versions USING btree (status);


--
-- Name: ix_budget_versions_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_budget_versions_year ON public.budget_versions USING btree (year);


--
-- Name: ix_contractors_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_contractors_department_id ON public.contractors USING btree (department_id);


--
-- Name: ix_contractors_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_contractors_id ON public.contractors USING btree (id);


--
-- Name: ix_contractors_inn; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_contractors_inn ON public.contractors USING btree (inn);


--
-- Name: ix_contractors_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_contractors_is_active ON public.contractors USING btree (is_active);


--
-- Name: ix_contractors_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_contractors_name ON public.contractors USING btree (name);


--
-- Name: ix_dashboard_configs_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dashboard_configs_id ON public.dashboard_configs USING btree (id);


--
-- Name: ix_dashboard_configs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dashboard_configs_user_id ON public.dashboard_configs USING btree (user_id);


--
-- Name: ix_departments_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_departments_code ON public.departments USING btree (code);


--
-- Name: ix_departments_ftp_subdivision_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_departments_ftp_subdivision_name ON public.departments USING btree (ftp_subdivision_name);


--
-- Name: ix_departments_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_departments_id ON public.departments USING btree (id);


--
-- Name: ix_departments_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);


--
-- Name: ix_employee_kpi_goals_employee_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_employee_kpi_goals_employee_id ON public.employee_kpi_goals USING btree (employee_id);


--
-- Name: ix_employee_kpi_goals_employee_kpi_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_employee_kpi_goals_employee_kpi_id ON public.employee_kpi_goals USING btree (employee_kpi_id);


--
-- Name: ix_employee_kpi_goals_goal_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_employee_kpi_goals_goal_id ON public.employee_kpi_goals USING btree (goal_id);


--
-- Name: ix_employee_kpi_goals_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_employee_kpi_goals_id ON public.employee_kpi_goals USING btree (id);


--
-- Name: ix_employee_kpi_goals_month; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_employee_kpi_goals_month ON public.employee_kpi_goals USING btree (month);


--
-- Name: ix_employee_kpi_goals_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_employee_kpi_goals_year ON public.employee_kpi_goals USING btree (year);


--
-- Name: ix_employee_kpis_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_employee_kpis_department_id ON public.employee_kpis USING btree (department_id);


--
-- Name: ix_employee_kpis_employee_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_employee_kpis_employee_id ON public.employee_kpis USING btree (employee_id);


--
-- Name: ix_employee_kpis_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_employee_kpis_id ON public.employee_kpis USING btree (id);


--
-- Name: ix_employee_kpis_month; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_employee_kpis_month ON public.employee_kpis USING btree (month);


--
-- Name: ix_employee_kpis_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_employee_kpis_year ON public.employee_kpis USING btree (year);


--
-- Name: ix_employees_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_employees_department_id ON public.employees USING btree (department_id);


--
-- Name: ix_employees_employee_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_employees_employee_number ON public.employees USING btree (employee_number);


--
-- Name: ix_employees_full_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_employees_full_name ON public.employees USING btree (full_name);


--
-- Name: ix_employees_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_employees_id ON public.employees USING btree (id);


--
-- Name: ix_employees_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_employees_status ON public.employees USING btree (status);


--
-- Name: ix_expenses_category_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_expenses_category_id ON public.expenses USING btree (category_id);


--
-- Name: ix_expenses_contractor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_expenses_contractor_id ON public.expenses USING btree (contractor_id);


--
-- Name: ix_expenses_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_expenses_department_id ON public.expenses USING btree (department_id);


--
-- Name: ix_expenses_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_expenses_id ON public.expenses USING btree (id);


--
-- Name: ix_expenses_is_closed; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_expenses_is_closed ON public.expenses USING btree (is_closed);


--
-- Name: ix_expenses_is_paid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_expenses_is_paid ON public.expenses USING btree (is_paid);


--
-- Name: ix_expenses_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_expenses_number ON public.expenses USING btree (number);


--
-- Name: ix_expenses_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_expenses_organization_id ON public.expenses USING btree (organization_id);


--
-- Name: ix_expenses_request_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_expenses_request_date ON public.expenses USING btree (request_date);


--
-- Name: ix_expenses_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_expenses_status ON public.expenses USING btree (status);


--
-- Name: ix_forecast_expenses_category_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_forecast_expenses_category_id ON public.forecast_expenses USING btree (category_id);


--
-- Name: ix_forecast_expenses_contractor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_forecast_expenses_contractor_id ON public.forecast_expenses USING btree (contractor_id);


--
-- Name: ix_forecast_expenses_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_forecast_expenses_department_id ON public.forecast_expenses USING btree (department_id);


--
-- Name: ix_forecast_expenses_forecast_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_forecast_expenses_forecast_date ON public.forecast_expenses USING btree (forecast_date);


--
-- Name: ix_forecast_expenses_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_forecast_expenses_id ON public.forecast_expenses USING btree (id);


--
-- Name: ix_forecast_expenses_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_forecast_expenses_organization_id ON public.forecast_expenses USING btree (organization_id);


--
-- Name: ix_kpi_goals_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kpi_goals_category ON public.kpi_goals USING btree (category);


--
-- Name: ix_kpi_goals_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kpi_goals_department_id ON public.kpi_goals USING btree (department_id);


--
-- Name: ix_kpi_goals_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kpi_goals_id ON public.kpi_goals USING btree (id);


--
-- Name: ix_kpi_goals_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kpi_goals_name ON public.kpi_goals USING btree (name);


--
-- Name: ix_kpi_goals_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kpi_goals_status ON public.kpi_goals USING btree (status);


--
-- Name: ix_kpi_goals_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kpi_goals_year ON public.kpi_goals USING btree (year);


--
-- Name: ix_organizations_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_organizations_department_id ON public.organizations USING btree (department_id);


--
-- Name: ix_organizations_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_organizations_id ON public.organizations USING btree (id);


--
-- Name: ix_organizations_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_organizations_is_active ON public.organizations USING btree (is_active);


--
-- Name: ix_organizations_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_organizations_name ON public.organizations USING btree (name);


--
-- Name: ix_payroll_actuals_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payroll_actuals_department_id ON public.payroll_actuals USING btree (department_id);


--
-- Name: ix_payroll_actuals_employee_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payroll_actuals_employee_id ON public.payroll_actuals USING btree (employee_id);


--
-- Name: ix_payroll_actuals_expense_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payroll_actuals_expense_id ON public.payroll_actuals USING btree (expense_id);


--
-- Name: ix_payroll_actuals_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payroll_actuals_id ON public.payroll_actuals USING btree (id);


--
-- Name: ix_payroll_actuals_month; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payroll_actuals_month ON public.payroll_actuals USING btree (month);


--
-- Name: ix_payroll_actuals_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payroll_actuals_year ON public.payroll_actuals USING btree (year);


--
-- Name: ix_payroll_plans_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payroll_plans_department_id ON public.payroll_plans USING btree (department_id);


--
-- Name: ix_payroll_plans_employee_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payroll_plans_employee_id ON public.payroll_plans USING btree (employee_id);


--
-- Name: ix_payroll_plans_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payroll_plans_id ON public.payroll_plans USING btree (id);


--
-- Name: ix_payroll_plans_month; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payroll_plans_month ON public.payroll_plans USING btree (month);


--
-- Name: ix_payroll_plans_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payroll_plans_year ON public.payroll_plans USING btree (year);


--
-- Name: ix_salary_history_employee_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_salary_history_employee_id ON public.salary_history USING btree (employee_id);


--
-- Name: ix_salary_history_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_salary_history_id ON public.salary_history USING btree (id);


--
-- Name: ix_users_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_department_id ON public.users USING btree (department_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: attachments attachments_expense_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attachments
    ADD CONSTRAINT attachments_expense_id_fkey FOREIGN KEY (expense_id) REFERENCES public.expenses(id) ON DELETE CASCADE;


--
-- Name: audit_logs audit_logs_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: budget_approval_log budget_approval_log_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_approval_log
    ADD CONSTRAINT budget_approval_log_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.budget_versions(id) ON DELETE CASCADE;


--
-- Name: budget_plan_details budget_plan_details_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_plan_details
    ADD CONSTRAINT budget_plan_details_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.budget_categories(id);


--
-- Name: budget_plan_details budget_plan_details_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_plan_details
    ADD CONSTRAINT budget_plan_details_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.budget_versions(id) ON DELETE CASCADE;


--
-- Name: budget_plans budget_plans_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_plans
    ADD CONSTRAINT budget_plans_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.budget_categories(id);


--
-- Name: budget_scenarios budget_scenarios_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_scenarios
    ADD CONSTRAINT budget_scenarios_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: budget_versions budget_versions_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_versions
    ADD CONSTRAINT budget_versions_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: budget_versions budget_versions_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_versions
    ADD CONSTRAINT budget_versions_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.budget_scenarios(id);


--
-- Name: employee_kpi_goals employee_kpi_goals_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_kpi_goals
    ADD CONSTRAINT employee_kpi_goals_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- Name: employee_kpi_goals employee_kpi_goals_employee_kpi_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_kpi_goals
    ADD CONSTRAINT employee_kpi_goals_employee_kpi_id_fkey FOREIGN KEY (employee_kpi_id) REFERENCES public.employee_kpis(id);


--
-- Name: employee_kpi_goals employee_kpi_goals_goal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_kpi_goals
    ADD CONSTRAINT employee_kpi_goals_goal_id_fkey FOREIGN KEY (goal_id) REFERENCES public.kpi_goals(id);


--
-- Name: employee_kpis employee_kpis_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_kpis
    ADD CONSTRAINT employee_kpis_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: employee_kpis employee_kpis_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_kpis
    ADD CONSTRAINT employee_kpis_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- Name: employees employees_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: expenses expenses_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.budget_categories(id);


--
-- Name: expenses expenses_contractor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_contractor_id_fkey FOREIGN KEY (contractor_id) REFERENCES public.contractors(id);


--
-- Name: expenses expenses_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: budget_categories fk_budget_categories_department_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_categories
    ADD CONSTRAINT fk_budget_categories_department_id FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: budget_categories fk_budget_categories_parent_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_categories
    ADD CONSTRAINT fk_budget_categories_parent_id FOREIGN KEY (parent_id) REFERENCES public.budget_categories(id);


--
-- Name: budget_plans fk_budget_plans_department_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_plans
    ADD CONSTRAINT fk_budget_plans_department_id FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: contractors fk_contractors_department_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contractors
    ADD CONSTRAINT fk_contractors_department_id FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: dashboard_configs fk_dashboard_configs_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dashboard_configs
    ADD CONSTRAINT fk_dashboard_configs_user_id FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: expenses fk_expenses_department_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT fk_expenses_department_id FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: forecast_expenses fk_forecast_expenses_department_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.forecast_expenses
    ADD CONSTRAINT fk_forecast_expenses_department_id FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: organizations fk_organizations_department_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT fk_organizations_department_id FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: users fk_users_department_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_department_id FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: forecast_expenses forecast_expenses_based_on_expense_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.forecast_expenses
    ADD CONSTRAINT forecast_expenses_based_on_expense_id_fkey FOREIGN KEY (based_on_expense_id) REFERENCES public.expenses(id);


--
-- Name: forecast_expenses forecast_expenses_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.forecast_expenses
    ADD CONSTRAINT forecast_expenses_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.budget_categories(id);


--
-- Name: forecast_expenses forecast_expenses_contractor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.forecast_expenses
    ADD CONSTRAINT forecast_expenses_contractor_id_fkey FOREIGN KEY (contractor_id) REFERENCES public.contractors(id);


--
-- Name: forecast_expenses forecast_expenses_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.forecast_expenses
    ADD CONSTRAINT forecast_expenses_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: kpi_goals kpi_goals_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kpi_goals
    ADD CONSTRAINT kpi_goals_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: payroll_actuals payroll_actuals_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_actuals
    ADD CONSTRAINT payroll_actuals_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: payroll_actuals payroll_actuals_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_actuals
    ADD CONSTRAINT payroll_actuals_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- Name: payroll_actuals payroll_actuals_expense_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_actuals
    ADD CONSTRAINT payroll_actuals_expense_id_fkey FOREIGN KEY (expense_id) REFERENCES public.expenses(id);


--
-- Name: payroll_plans payroll_plans_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_plans
    ADD CONSTRAINT payroll_plans_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: payroll_plans payroll_plans_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_plans
    ADD CONSTRAINT payroll_plans_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- Name: salary_history salary_history_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.salary_history
    ADD CONSTRAINT salary_history_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- PostgreSQL database dump complete
--


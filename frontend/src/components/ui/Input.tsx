import React from 'react'
import { Input as AntInput, InputProps as AntInputProps } from 'antd'
import { cn } from '@/utils/cn'

export interface InputProps extends AntInputProps {
  error?: boolean
}

const InputComponent: React.FC<InputProps> = ({ 
  className, 
  error, 
  ...props 
}) => {
  return (
    <AntInput
      className={cn(
        'rounded-lg border-gray-300 hover:border-primary focus:border-primary transition-colors',
        error && 'border-red-500 hover:border-red-500 focus:border-red-500',
        className
      )}
      {...props}
    />
  )
}

const Password: React.FC<InputProps> = ({ 
  className, 
  error, 
  ...props 
}) => {
  return (
    <AntInput.Password
      className={cn(
        'rounded-lg border-gray-300 hover:border-primary focus:border-primary transition-colors',
        error && 'border-red-500 hover:border-red-500 focus:border-red-500',
        className
      )}
      {...props}
    />
  )
}

type InputType = typeof InputComponent & {
  Password: typeof Password
}

export const Input = InputComponent as InputType
Input.Password = Password

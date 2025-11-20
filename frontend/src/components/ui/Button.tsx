import React from 'react'
import { Button as AntButton, ButtonProps as AntButtonProps } from 'antd'
import { cn } from '@/utils/cn'

export interface ButtonProps extends Omit<AntButtonProps, 'variant'> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
}

export const Button: React.FC<ButtonProps> = ({ 
  children, 
  className, 
  variant = 'primary', 
  type,
  ...props 
}) => {
  // Map variants to Ant Design types where possible, or use custom classes
  const getAntType = (): AntButtonProps['type'] => {
    if (variant === 'primary') return 'primary'
    if (variant === 'outline') return 'default'
    if (variant === 'ghost') return 'text'
    if (variant === 'danger') return 'primary' // We'll override color with class
    return 'default'
  }

  return (
    <AntButton
      type={type || getAntType()}
      className={cn(
        // Base styles can be added here
        variant === 'danger' && 'bg-red-500 hover:!bg-red-600 border-red-500 hover:!border-red-600',
        className
      )}
      {...props}
    >
      {children}
    </AntButton>
  )
}

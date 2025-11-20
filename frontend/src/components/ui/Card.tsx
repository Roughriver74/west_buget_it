import React from 'react'
import { Card as AntCard, CardProps as AntCardProps } from 'antd'
import { cn } from '@/utils/cn'

export interface CardProps extends Omit<AntCardProps, 'variant'> {
  noPadding?: boolean
  variant?: 'default' | 'glass' | 'borderless'
}

export const Card: React.FC<CardProps> = ({ 
  children, 
  className, 
  noPadding = false,
  variant = 'default',
  ...props 
}) => {
  return (
    <AntCard
      className={cn(
        'rounded-xl transition-all duration-300',
        variant === 'default' && 'bg-white dark:bg-[#1e293b] shadow-sm border-gray-100 dark:border-[#334155]',
        variant === 'glass' && 'glass-card',
        variant === 'borderless' && '!border-none !shadow-none bg-transparent',
        noPadding && '[&>.ant-card-body]:p-0',
        className
      )}
      bordered={variant !== 'borderless' && variant !== 'glass'}
      {...props}
    >
      {children}
    </AntCard>
  )
}

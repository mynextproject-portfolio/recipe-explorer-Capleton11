import { Badge } from '@/components/ui/Badge'

interface SourceBadgeProps {
  source: string
}

export function SourceBadge({ source }: SourceBadgeProps) {
  const isMealDB = source?.toLowerCase().includes('mealdb')
  return (
    <Badge variant={isMealDB ? 'warning' : 'success'}>
      {isMealDB ? 'TheMealDB' : 'My Recipes'}
    </Badge>
  )
}

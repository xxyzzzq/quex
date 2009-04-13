/* -*- C++ -*- vim: set syntax=cpp: */
#ifndef __INCLUDE_GUARD_QUEX__CODE_BASE__POST_CATEGORIZER_I__
#define __INCLUDE_GUARD_QUEX__CODE_BASE__POST_CATEGORIZER_I__
#ifdef  QUEX_OPTION_POST_CATEGORIZER

#include <quex/code_base/MemoryManager>
#include <quex/code_base/template/PostCategorizer>

namespace quex {

    inline QuexPostCategorizerNode* 
    QuexPostCategorizerNode_new(QUEX_TYPE_CHARACTER         FirstCharacter,
                                const QUEX_TYPE_CHARACTER*  Remainder,
                                QUEX_TYPE_TOKEN_ID          TokenID)
    {
        QuexPostCategorizerNode* me = MemoryManager_PostCategorizerNode_allocate(__QUEX_STD_strlen(Remainder));
        me->name_first_character = FirstCharacter;
        me->name_remainder       = Remainder;
        me->token_id             = TokenID;
        me->lesser  = 0x0;
        me->greater = 0x0;
        return me;
    }

    inline int
    QuexPostCategorizerNode_compare(QuexPostCategorizerNode*    me, 
                                    QUEX_TYPE_CHARACTER         FirstCharacter, 
                                    const QUEX_TYPE_CHARACTER*  Remainder)
    {
        if     ( FirstCharacter > me->name_first_character ) return 1;
        else if( FirstCharacter < me->name_first_character ) return -1;
        else                                                 return strcmp(Remainder, me->name_remainder);
    }

    inline void
    QuexPostCategorizer_construct(QuexPostCategorizer* me)
    {
        me->root = 0x0;
    }

    inline QuexPostCategorizerNode*
    QuexPostCategorizer_find(QuexPostCategorizer* me, const QUEX_TYPE_CHARACTER* EntryName)
    {
        QUEX_TYPE_CHARACTER         FirstCharacter = EntryName[0];
        const QUEX_TYPE_CHARACTER*  Remainder = FirstCharacter == 0x0 ? 0x0 : EntryName + 1;
        QuexPostCategorizerNode*    node = me->root;

        while( node != 0x0 ) {
            int result = QuexPostCategorizerNode_compare(node, FirstCharacter, Remainder);
            if     ( result == 1 )  node = node->greater;
            else if( result == -1 ) node = node->lesser;
            else                    return node;
        }
        return 0x0;
    }

    inline void
    QuexPostCategorizer_insert(QuexPostCategorizer* me, 
                               const QUEX_TYPE_CHARACTER* EntryName, QUEX_TYPE_TOKEN_ID TokenID)
    {
        QUEX_TYPE_CHARACTER         FirstCharacter = EntryName[0];
        const QUEX_TYPE_CHARACTER*  Remainder = FirstCharacter == 0x0 ? 0x0 : EntryName + 1;
        QuexPostCategorizerNode*  node      = me->root;
        QuexPostCategorizerNode*  prev_node = 0x0;
        int                       result = 0;

        if( me->root == 0x0 ) {
            me->root = QuexPostCategorizerNode_new(FirstCharacter, Remainder, TokenID);
            return;
        }
        while( node != 0x0 ) {
            prev_node = node;
            result    = QuexPostCategorizerNode_compare(node, FirstCharacter, Remainder);
            if     ( result == 1 )  node = node->greater;
            else if( result == -1 ) node = node->lesser;
            else                    return; /* Node with that name already exists */
        }
        __quex_assert( prev_node != 0x0 );
        __quex_assert( result != 0 );

        if( result == 1 ) 
            prev_node->greater = QuexPostCategorizerNode_new(FirstCharacter, Remainder, TokenID);
        else 
            prev_node->lesser  = QuexPostCategorizerNode_new(FirstCharacter, Remainder, TokenID);
    }

    inline void
    QuexPostCategorizer_delete(QuexPostCategorizer* me, const QUEX_TYPE_CHARACTER* EntryName)
    {
        int result = 0;
        QUEX_TYPE_CHARACTER         FirstCharacter = EntryName[0];
        const QUEX_TYPE_CHARACTER*  Remainder = FirstCharacter == 0x0 ? 0x0 : EntryName + 1;
        QuexPostCategorizerNode*  node   = 0x0;
        QuexPostCategorizerNode*  parent = 0x0;
        QuexPostCategorizerNode*  found  = me->root;

        __quex_assert( found != 0x0 );
        while( 1 + 1 == 2 ) {
            result = QuexPostCategorizerNode_compare(found, FirstCharacter, Remainder);
           
            /* result == 0: found's name == EntryName 
             * On 'break': If found == root then parent = 0x0 which triggers a special treatment. */
            if( result == 0 ) break;

            parent = found;

            if     ( result == 1 )  found = found->greater;
            else if( result == -1 ) found = found->lesser;

            if( found == 0x0 ) return; /* Not found name with that name */
        };
        /* Found a node with 'EntryName' */

        /* Remove node and re-order tree */
        if( found == parent->lesser ) {
            /* (1) 'found' is the 'lesser' child of the parent:
             *
             *                 (parent's greater tree)
             *                /
             *        (parent)        (greater tree)
             *               \       /
             *                (found)
             *                       \
             *                        (lesser tree)
             *
             *     All subnodes of (greater tree) are greater than all subnodes in (lesser tree).
             *     => (i) mount (lesser tree) to the least node of (greater tree).                */
            for(node = found->greater; node->lesser != 0x0; node = node->lesser );
            node->lesser = found->lesser;
            /*     Anything in the subtree of 'found' is lesser than anything in 'parent's 
             *     greater tree.
             *     => (ii) mount (greater tree) to the least node of the (parent's greater tree). */
            if( parent != 0x0 ) {
                for(node = parent->greater; node->lesser != 0x0; node = node->lesser );
                node->lesser = found->lesser;
            }
        } else {
            /* (2) 'found' is the 'greater' child of the parent:
             *
             *     (i)  mount (greater tree) to the greatest node of (greater tree).                  */
            for(node = found->lesser; node->greater != 0x0; node = node->greater );
            node->greater = found->greater;
            /*     (ii) mount (greater tree) to the greatest node of the (parent's greater tree).    */
            if( parent != 0x0 ) {
                for(node = parent->lesser; node->greater != 0x0; node = node->greater );
                node->greater = found->greater;
            }
        }
        MemoryManager_PostCategorizerNode_free(found);
    }

    inline void
    QuexPostCategorizer_print_tree(QuexPostCategorizerNode* node, int Depth)
    {
        if( node == 0x0 ) {
            for(int i=0; i<Depth; ++i) __QUEX_STD_printf("        ");
            __QUEX_STD_printf("[EMPTY]\n");
            return;
        }

        QuexPostCategorizer_print_tree(node->greater, Depth + 1);

        for(int i=0; i < Depth + 1; ++i) __QUEX_STD_printf("        ");
        __QUEX_STD_printf("/\n");

        for(int i=0; i<Depth; ++i) __QUEX_STD_printf("        ");
        __QUEX_STD_printf("[%c]%s: %i\n", node->name_first_character, node->name_remainder, (int)node->token_id);

        for(int i=0; i<Depth + 1; ++i) __QUEX_STD_printf("        ");
        __QUEX_STD_printf("\\\n");

        QuexPostCategorizer_print_tree(node->lesser, Depth + 1);
    }
}
#include <quex/code_base/MemoryManager.i>

#endif /* QUEX_OPTION_POST_CATEGORIZER */
#endif /* __INCLUDE_GUARD_QUEX__CODE_BASE__POST_CATEGORIZER_I__ */
